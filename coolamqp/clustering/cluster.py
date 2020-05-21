# coding=UTF-8
"""
THE object you interface with
"""
from __future__ import print_function, absolute_import, division

import logging
import time
import typing as tp
import warnings
from concurrent.futures import Future

from coolamqp.utils import monotonic
import six

from coolamqp.attaches import Publisher, AttacheGroup, Consumer, Declarer
from coolamqp.attaches.utils import close_future
from coolamqp.clustering.events import ConnectionLost, MessageReceived, \
    NothingMuch, Event
from coolamqp.clustering.single import SingleNodeReconnector
from coolamqp.exceptions import ConnectionDead
from coolamqp.objects import Exchange, Message, Queue, FrameLogger
from coolamqp.uplink import ListenerThread

logger = logging.getLogger(__name__)

THE_POPE_OF_NOPE = NothingMuch()


# If any spans are spawn here, it's Cluster's job to finish them, except for publish()
class Cluster(object):
    """
    Frontend for your AMQP needs.

    This has ListenerThread.

    Call .start() to connect to AMQP.

    It is not safe to fork() after .start() is called, but it's OK before.

    :param nodes: list of nodes, or a single node. For now, only one is supported.
    :param on_fail: callable/0 to call when connection fails in an
        unclean way. This is a one-shot
    :param extra_properties: refer to documentation in [/coolamqp/connection/connection.py]
        Connection.__init__
    :param log_frames: an object that supports logging each and every frame CoolAMQP sends and
        receives from the broker
    :param name: name to appear in log items and prctl() for the listener thread
    :param on_blocked: callable to call when ConnectionBlocked/ConnectionUnblocked is received. It will be
        called with a value of True if connection becomes blocked, and False upon an unblock
    :param tracer: tracer, if opentracing is installed
    """

    # Events you can be informed about
    ST_LINK_LOST = 0  # Link has been lost
    ST_LINK_REGAINED = 1  # Link has been regained

    def __init__(self, nodes,  # type: tp.Union[NodeDefinition, tp.List[NodeDefinition]]
                 on_fail=None,  # type: tp.Optional[tp.Callable[[], None]]
                 extra_properties=None,  # type: tp.Optional[tp.List[tp.Tuple[bytes, tp.Tuple[bytes, str]]]]
                 log_frames=None,  # type: tp.Optional[FrameLogger]
                 name=None,  # type: tp.Optional[str]
                 on_blocked=None,  # type: tp.Callable[[bool], None],
                 tracer=None        # type: opentracing.Traccer
                 ):
        from coolamqp.objects import NodeDefinition
        if isinstance(nodes, NodeDefinition):
            nodes = [nodes]

        if len(nodes) > 1:
            raise NotImplementedError(u'Multiple nodes not supported yet')

        if tracer is not None:
            try:
                import opentracing
            except ImportError:
                raise RuntimeError('tracer given, but opentracing is not installed!')

        self.tracer = tracer
        self.name = name or 'CoolAMQP'
        self.node, = nodes
        self.extra_properties = extra_properties
        self.log_frames = log_frames
        self.on_blocked = on_blocked
        self.connected = False

        if on_fail is not None:
            def decorated():
                if not self.listener.terminating and self.connected:
                    on_fail()

            self.on_fail = decorated
        else:
            self.on_fail = None

    def declare(self, obj,  # type: tp.Union[Queue, Exchange]
                persistent=False,  # type: bool
                span=None       # type: tp.Optional[opentracing.Span]
                ):  # type: (...) -> concurrent.futures.Future
        """
        Declare a Queue/Exchange

        :param obj: Queue/Exchange object
        :param persistent: should it be redefined upon reconnect?
        :param span: optional parent span, if opentracing is installed
        :return: Future
        """
        if span is not None:
            child_span = self._make_span('declare', span)
        else:
            child_span = None
        fut = self.decl.declare(obj, persistent=persistent, span=child_span)
        return close_future(fut, child_span)

    def drain(self, timeout, span=None):  # type: (float) -> Event
        """
        Return an Event.

        :param timeout: time to wait for an event. 0 means return immediately. None means block forever
        :para span: optional parent span, if opentracing is installed
        :return: an Event instance. NothingMuch is returned when there's nothing within a given timoeout
        """
        def fetch():
            try:
                if timeout == 0:
                    return self.events.get_nowait()
                else:
                    return self.events.get(True, timeout)
            except six.moves.queue.Empty:
                return THE_POPE_OF_NOPE

        if span is not None:
            from opentracing import tags
            parent_span = self.tracer.start_active_span('AMQP call',
                                                        child_of=span,
                                          tags={
                                          tags.SPAN_KIND: tags.SPAN_KIND_RPC_CLIENT,
                                          tags.DATABASE_TYPE: 'amqp',
                                          tags.DATABASE_STATEMENT: 'drain'
            })

            with parent_span:
                return fetch()
        else:
            return fetch()

    def consume(self, queue, on_message=None, span=None, *args, **kwargs):
        # type: (Queue, tp.Callable[[MessageReceived], None] -> tp.Tuple[Consumer, Future]
        """
        Start consuming from a queue.

        args and kwargs will be passed to Consumer constructor (coolamqp.attaches.consumer.Consumer).
        Don't use future_to_notify - it's done here!

        Take care not to lose the Consumer object - it's the only way to cancel a consumer!

        :param queue: Queue object, being consumed from right now.
            Note that name of anonymous queue might change at any time!
        :param on_message: callable that will process incoming messages
                           if you leave it at None, messages will be .put into self.events
        :param span: optional span, if opentracing is installed
        :return: a tuple (Consumer instance, and a Future), that tells, when consumer is ready
        """
        if span is not None:
            child_span = self._make_span('consume', span)
        else:
            child_span = None
        fut = Future()
        fut.set_running_or_notify_cancel()  # it's running right now
        on_message = on_message or (
            lambda rmsg: self.events.put_nowait(MessageReceived(rmsg)))
        con = Consumer(queue, on_message, future_to_notify=fut, span=span, *args,
                       **kwargs)
        self.attache_group.add(con)
        return con, close_future(fut, child_span)

    def delete_queue(self, queue):  # type: (coolamqp.objects.Queue) -> Future
        """
        Delete a queue.

        :param queue: Queue instance that represents what to delete
        :return: a Future (will succeed with None or fail with AMQPError)
        """
        return self.decl.delete_queue(queue)

    def _make_span(self, call, span):
        try:
            from opentracing import tags
        except ImportError:
            pass
        else:
            return self.tracer.start_span('AMQP call',
                                          child_of=span,
                                          tags={
                                              tags.SPAN_KIND: tags.SPAN_KIND_RPC_CLIENT,
                                              tags.DATABASE_TYPE: 'amqp',
                                              tags.DATABASE_STATEMENT: call
                                          })

    def publish(self, message,  # type: Message
                exchange=None,  # type: tp.Union[Exchange, str, bytes]
                routing_key=u'',  # type: tp.Union[str, bytes]
                tx=None,  # type: tp.Optional[bool]
                confirm=None,  # type: tp.Optional[bool]
                span=None       # type: tp.Optional[opentracing.Span]
                ):  # type: (...) -> tp.Optional[Future]
        """
        Publish a message.

        :param message: Message to publish
        :param exchange: exchange to use. Default is the "direct" empty-name exchange.
        :param routing_key: routing key to use
        :param confirm: Whether to publish it using confirms/transactions.
                        If you choose so, you will receive a Future that can be used
                        to check it broker took responsibility for this message.
                        Note that if tx if False, and message cannot be delivered to broker at once,
                        it will be discarded
        :param tx: deprecated, alias for confirm
        :param span: optionally, current span, if opentracing is installed
        :return: Future to be finished on completion or None, is confirm/tx was not chosen
        """
        if self.tracer is not None:
            span = self._make_span('publish', span)

        if isinstance(exchange, Exchange):
            exchange = exchange.name.encode('utf8')
        elif exchange is None:
            exchange = b''
        elif isinstance(exchange, six.text_type):
            exchange = exchange.encode('utf8')

        if isinstance(routing_key, six.text_type):
            routing_key = routing_key.encode('utf8')

        if tx is not None:  # confirm is a drop-in replacement. tx is unfortunately named
            warnings.warn(u'Use confirm kwarg instead', DeprecationWarning)

            if confirm is not None:
                raise RuntimeError(
                    u'Using both tx= and confirm= at once does not make sense')
        elif confirm is not None:
            tx = confirm
        else:
            tx = False

        try:
            return (self.pub_tr if tx else self.pub_na).publish(message,
                                                                exchange,
                                                                routing_key,
                                                                span)
        except Publisher.UnusablePublisher:
            raise NotImplementedError(
                u'Sorry, this functionality is not yet implemented!')

    def start(self, wait=True, timeout=10.0, log_frames=None):  # type: (bool, float, bool) -> None
        """
        Connect to broker. Initialize Cluster.

        Only after this call is Cluster usable.
        It is not safe to fork after this.

        :param wait: block until connection is ready
        :param timeout: timeout to wait until the connection is ready. If it is not, a
                        ConnectionDead error will be raised
        :raise RuntimeError: called more than once
        :raise ConnectionDead: failed to connect within timeout
        :param log_frames: whether to keep a log of sent/received frames in self.log_frames
        """

        try:
            self.listener
        except AttributeError:
            pass
        else:
            raise RuntimeError(u'[%s] This was already called!' % (self.name,))

        self.listener = ListenerThread(name=self.name)

        self.attache_group = AttacheGroup()

        self.events = six.moves.queue.Queue()  # for coolamqp.clustering.events.*

        self.snr = SingleNodeReconnector(self.node, self.attache_group,
                                         self.listener, self.extra_properties,
                                         log_frames, self.name)
        self.snr.on_fail.add(lambda: self.events.put_nowait(ConnectionLost()))
        if self.on_fail is not None:
            self.snr.on_fail.add(self.on_fail)

        if self.on_blocked is not None:
            self.snr.on_blocked.add(self.on_blocked)

        # Spawn a transactional publisher and a noack publisher
        self.pub_tr = Publisher(Publisher.MODE_CNPUB, self)
        self.pub_na = Publisher(Publisher.MODE_NOACK, self)
        self.decl = Declarer(self)

        self.attache_group.add(self.pub_tr)
        self.attache_group.add(self.pub_na)
        self.attache_group.add(self.decl)

        self.listener.init()
        self.listener.start()
        self.snr.connect(timeout=timeout)

        if wait:
            # this is only going to take a short amount of time, so we're fine with polling
            start_at = monotonic()
            while not self.connected and monotonic() - start_at < timeout:
                time.sleep(0.1)
            if not self.connected:
                raise ConnectionDead(
                    '[%s] Could not connect within %s seconds' % (self.name, timeout,))

    def shutdown(self, wait=True):  # type: (bool) -> None
        """
        Terminate all connections, release resources - finish the job.

        :param wait: block until this is done
        :raise RuntimeError: if called without start() being called first
        """
        self.connected = False
        try:
            self.listener
        except AttributeError:
            raise RuntimeError(u'shutdown without start')

        logger.info('[%s] Commencing shutdown', self.name)

        self.listener.terminate()
        if wait:
            self.listener.join()
