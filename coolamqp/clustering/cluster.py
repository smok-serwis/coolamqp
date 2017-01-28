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
from coolamqp.attaches import Publisher, AttacheGroup, Consumer, Declarer
from coolamqp.objects import Exchange
from concurrent.futures import Future

from coolamqp.clustering.events import ConnectionLost, MessageReceived, NothingMuch

logger = logging.getLogger(__name__)

THE_POPE_OF_NOPE = NothingMuch()


class Cluster(object):
    """
    Frontend for your AMQP needs.

    This has ListenerThread.

    Call .start() to connect to AMQP.

    It is not safe to fork() after .start() is called, but it's OK before.
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

        self.node, = nodes

    def declare(self, obj, persistent=False):
        """
        Declare a Queue/Exchange
        :param obj: Queue/Exchange object
        :param persistent: should it be redefined upon reconnect?
        :return: Future
        """
        return self.decl.declare(obj, persistent=persistent)

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
        fut.set_running_or_notify_cancel()  # it's running right now
        on_message = on_message or (lambda rmsg: self.events.put_nowait(MessageReceived(rmsg)))
        con = Consumer(queue, on_message, future_to_notify=fut, *args, **kwargs)
        self.attache_group.add(con)
        return con, fut

    def publish(self, message, exchange=None, routing_key=u'', tx=None, confirm=None):
        """
        Publish a message.

        :param message: Message to publish
        :param exchange: exchange to use. Default is the "direct" empty-name exchange.
        :type exchange: unicode/bytes (exchange name) or Exchange object.
        :param routing_key: routing key to use
        :param confirm: Whether to publish it using confirms/transactions.
                        If you choose so, you will receive a Future that can be used
                        to check it broker took responsibility for this message.
                        Note that if tx if False, and message cannot be delivered to broker at once,
                        it will be discarded.
        :param tx: deprecated, alias for confirm
        :return: Future or None
        """
        if isinstance(exchange, Exchange):
            exchange = exchange.name.encode('utf8')
        elif exchange is None:
            exchange = b''
        else:
            exchange = exchange.encode('utf8')

        if tx is not None:  # confirm is a drop-in replacement. tx is unfortunately named
            warnings.warn(u'Use confirm kwarg instead', DeprecationWarning)

            if confirm is None:
                tx = False
            else:
                raise RuntimeError(u'Using both tx= and confirm= at once does not make sense')
        elif confirm is None:
            tx = False
        else:
            tx = confirm


        try:
            return (self.pub_tr if tx else self.pub_na).publish(message, exchange, routing_key.encode('utf8'))
        except Publisher.UnusablePublisher:
            raise NotImplementedError(u'Sorry, this functionality is not yet implemented!')


    def start(self, wait=True):
        """
        Connect to broker. Initialize Cluster.

        Only after this call is Cluster usable.
        It is not safe to fork after this.

        :param wait: block until connection is ready
        :raise RuntimeError: called more than once
        """

        try:
            self.listener
        except AttributeError:
            pass
        else:
            raise RuntimeError(u'This was already called!')

        self.listener = ListenerThread()

        self.attache_group = AttacheGroup()

        self.events = six.moves.queue.Queue()   # for coolamqp.clustering.events.*

        self.snr = SingleNodeReconnector(self.node, self.attache_group, self.listener)
        self.snr.on_fail.add(lambda: self.events.put_nowait(ConnectionLost()))

        # Spawn a transactional publisher and a noack publisher
        self.pub_tr = Publisher(Publisher.MODE_CNPUB)
        self.pub_na = Publisher(Publisher.MODE_NOACK)
        self.decl = Declarer()

        self.attache_group.add(self.pub_tr)
        self.attache_group.add(self.pub_na)
        self.attache_group.add(self.decl)


        self.listener.init()
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
        :raise RuntimeError: if called without start() being called first
        """

        try:
            self.listener
        except AttributeError:
            raise RuntimeError(u'shutdown without start')

        logger.info('Commencing shutdown')

        self.listener.terminate()
        if wait:
            self.listener.join()
