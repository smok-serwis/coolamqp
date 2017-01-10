# coding=UTF-8
"""
THE object you interface with
"""
from __future__ import print_function, absolute_import, division
import six
import logging
import warnings
import time
from coolamqp.uplink import ListenerThread
from coolamqp.clustering.single import SingleNodeReconnector
from coolamqp.attaches import Publisher, AttacheGroup, Consumer
from coolamqp.objects import Future, Exchange


from coolamqp.clustering.events import ConnectionLost, MessageReceived, NothingMuch

logger = logging.getLogger(__name__)

THE_POPE_OF_NOPE = NothingMuch()


class Cluster(object):
    """
    Frontend for your AMQP needs.

    This has ListenerThread.

    Call .start() to connect to AMQP.
    """

    # Events you can be informed about
    ST_LINK_LOST = 0            # Link has been lost
    ST_LINK_REGAINED = 1        # Link has been regained


    def __init__(self, nodes):
        """
        :param nodes: list of nodes, or a single node. For now, only one is supported.
        :type nodes: NodeDefinition instance or a list of NodeDefinition instances
        """
        from coolamqp.objects import NodeDefinition
        if isinstance(nodes, NodeDefinition):
            nodes = [nodes]

        if len(nodes) > 1:
            raise NotImplementedError(u'Multiple nodes not supported yet')

        self.listener = ListenerThread()
        self.node, = nodes

        self.attache_group = AttacheGroup()

        self.events = six.moves.queue.Queue()   # for coolamqp.clustering.events.*

        self.snr = SingleNodeReconnector(self.node, self.attache_group, self.listener)
        self.snr.on_fail.add(lambda: self.events.put_nowait(ConnectionLost()))

        # Spawn a transactional publisher and a noack publisher
        self.pub_tr = Publisher(Publisher.MODE_CNPUB)
        self.pub_na = Publisher(Publisher.MODE_NOACK)

        self.attache_group.add(self.pub_tr)
        self.attache_group.add(self.pub_na)

    def drain(self, timeout):
        """
        Return an Event.
        :param timeout: time to wait for an event. 0 means return immediately. None means block forever
        :return: an Event instance. NothingMuch is returned when there's nothing within a given timoeout
        """
        try:
            if timeout == 0:
                return self.events.get_nowait()
            else:
                return self.events.get(True, timeout)
        except six.moves.queue.Empty:
            return THE_POPE_OF_NOPE

    def consume(self, queue, on_message=None, *args, **kwargs):
        """
        Start consuming from a queue.

        args and kwargs will be passed to Consumer constructor (coolamqp.attaches.consumer.Consumer).
        Don't use future_to_notify - it's done here!

        Take care not to lose the Consumer object - it's the only way to cancel a consumer!

        :param queue: Queue object, being consumed from right now.
            Note that name of anonymous queue might change at any time!
        :param on_message: callable that will process incoming messages
                           if you leave it at None, messages will be .put into self.events
        :type on_message: callable(ReceivedMessage instance) or None
        :return: a tuple (Consumer instance, and a Future), that tells, when consumer is ready
        """
        fut = Future()
        on_message = on_message or (lambda rmsg: self.events.put_nowait(MessageReceived(rmsg)))
        con = Consumer(queue, on_message, future_to_notify=fut, *args, **kwargs)
        self.attache_group.add(con)
        return con, fut

    def publish(self, message, exchange=None, routing_key=u'', tx=False):
        """
        Publish a message.

        :param message: Message to publish
        :param exchange: exchange to use. Default is the "direct" empty-name exchange.
        :type exchange: unicode/bytes (exchange name) or Exchange object.
        :param routing_key: routing key to use
        :param tx: Whether to publish it transactionally.
                   If you choose so, you will receive a Future that can be used
                   to check it broker took responsibility for this message.
                   Note that if tx if False, and message cannot be delivered to broker at once,
                   it will be discarded.
        :return: Future or None
        """
        if isinstance(exchange, Exchange):
            exchange = exchange.name.encode('utf8')
        elif exchange is None:
            exchange = b''
        else:
            exchange = exchange.encode('utf8')

        try:
            return (self.pub_tr if tx else self.pub_na).publish(message, exchange, routing_key.encode('utf8'))
        except Publisher.UnusablePublisher:
            raise NotImplementedError(u'Sorry, this functionality is not yet implemented!')


    def start(self, wait=True):
        """
        Connect to broker.
        :param wait: block until connection is ready
        """
        self.listener.start()
        self.snr.connect()

        #todo not really elegant
        if wait:
            while not self.snr.is_connected():
                time.sleep(0.1)

    def shutdown(self, wait=True):
        """
        Terminate all connections, release resources - finish the job.
        :param wait: block until this is done
        """

        self.snr.shutdown()
        self.listener.terminate()
        if wait:
            self.listener.join()
