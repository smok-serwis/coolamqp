# coding=UTF-8
from __future__ import print_function, absolute_import, division

import logging
import time
import typing as tp
import warnings
from concurrent.futures import Future

import six

from coolamqp.argumentify import argumentify
from coolamqp.attaches import Publisher, AttacheGroup, Consumer, Declarer
from coolamqp.attaches.utils import close_future
from coolamqp.clustering.events import ConnectionLost, MessageReceived, \
    NothingMuch, Event
from coolamqp.clustering.single import SingleNodeReconnector
from coolamqp.exceptions import ConnectionDead
from coolamqp.objects import Exchange, Message, Queue, QueueBind
from coolamqp.uplink import ListenerThread
from coolamqp.utils import monotonic

logger = logging.getLogger(__name__)

nothing_much = NothingMuch()


# If any spans are spawn here, it's Cluster's job to finish them, except for publish()
class Cluster(object):
    """
    Frontend for your AMQP needs.

    This has ListenerThread.

    Call .start() to connect to AMQP.

    It is not safe to fork() after .start() is called, but it's OK before.
    """

    # Events you can be informed about
    ST_LINK_LOST = 0  # Link has been lost
    ST_LINK_REGAINED = 1  # Link has been regained

    def __init__(self, nodes,  # type: NodeDefinition
                 on_fail=None,  # type: tp.Optional[tp.Callable[[], None]]
                 extra_properties=None,
                 # type: tp.Optional[tp.List[tp.Tuple[bytes, tp.Tuple[bytes, str]]]]
                 log_frames=None,
                 name=None,  # type: tp.Optional[str]
                 on_blocked=None,  # type: tp.Callable[[bool], None],
                 tracer=None  # type: opentracing.Traccer
                 ):
        """
        :param nodes: single node
        :type nodes: NodeDefinition
        :param on_fail: callable/0 to call when connection fails in an
            unclean way. This is a one-shot
        :param extra_properties: refer to :class:`coolamqp.uplink.connection.Connection`
        :param log_frames: an object that supports logging each and every frame CoolAMQP sends and
            receives from the broker
        :type log_frames: tp.Optional[:class:`coolamqp.tracing.BaseFrameTracer`]
        :param name: name to appear in log items and prctl() for the listener thread
        :param on_blocked: callable to call when ConnectionBlocked/ConnectionUnblocked is received. It will be
            called with a value of True if connection becomes blocked, and False upon an unblock
        :param tracer: tracer, if opentracing is installed
        """
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

        self.started = False            # type: bool
        self.tracer = tracer
        self.name = name or 'CoolAMQP'  # type: str
        self.node, = nodes              # type: NodeDefinition
        self.extra_properties = extra_properties
        self.log_frames = log_frames
        self.on_blocked = on_blocked    # type: tp.Optional[tp.Callable[[bool], None]]
        self.connected = False          # type: bool
        self.listener = None            # type: BaseListener
        self.attache_group = None       # type: AttacheGroup
        self.events = None              # type: six.moves.queue.Queue
        self.snr = None                 # type: SingleNodeReconnector
        self.pub_tr = None              # type: Publisher
        self.pub_na = None              # type: Publisher
        self.decl = None                # type: Declarer
        self.on_fail = None

        if on_fail is not None:
            def decorated():
                if not self.listener.terminating and self.connected:
                    on_fail()

            self.on_fail = decorated

    def bind(self, queue, exchange, routing_key, span=None,
             dont_trace=False, arguments=None):
        """
        Bind a queue to an exchange

        :raise ValueError: cannot bind to anonymous queues
        """
        if queue.anonymous:
            raise ValueError('Canoot bind to anonymous queue')

        if span is not None and not dont_trace:
            child_span = self._make_span('bind', span)
        else:
            child_span = None
        fut = self.decl.declare(QueueBind(queue, exchange, routing_key, argumentify(arguments)),
                                span=child_span)
        return close_future(fut, child_span)

    def declare(self, obj,  # type: tp.Union[Queue, Exchange]
                span=None,  # type: tp.Optional[opentracing.Span]
                dont_trace=False    # type: bool
                ):  # type: (...) -> concurrent.futures.Future
        """
        Declare a Queue/Exchange.

        Non-anonymous queues have to be declared. Anonymous can't.

        .. note:: Note that if your queue relates to an exchange that has not yet been declared you'll be faced with
                  AMQP error 404: NOT_FOUND, so try to declare your exchanges before your queues.

        :param obj: Queue/Exchange object
        :param span: optional parent span, if opentracing is installed
        :param dont_trace: if True, a span won't be output
        :return: Future
        :raises ValueError: tried to declare an anonymous queue
        """
        if isinstance(obj, Queue) and obj.anonymous:
            raise ValueError('You cannot declare an anonymous queue!')
        if span is not None and not dont_trace:
            child_span = self._make_span('declare', span)
        else:
            child_span = None
        fut = self.decl.declare(obj, span=child_span)
        return close_future(fut, child_span)

    def drain(self, timeout, span=None, dont_trace=False):  # type: (float) -> Event
        """
        Return an Event.

        :param timeout: time to wait for an event. 0 means return immediately. None means block forever
        :param span: optional parent span, if opentracing is installed
        :param dont_trace: if True, this span won't be traced
        :return: an Event instance. NothingMuch is returned when there's nothing within a given timoeout
        """

        def fetch():
            try:
                if not timeout:
                    return self.events.get_nowait()
                else:
                    return self.events.get(True, timeout)
            except six.moves.queue.Empty:
                return nothing_much

        if span is not None and not dont_trace:
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

    def consume(self, queue, on_message=None, span=None,
                dont_trace=False,   # type: bool
                *args, **kwargs):
        # type: (Queue, tp.Callable[[MessageReceived], None]) -> tp.Tuple[Consumer, Future]
        """
        Start consuming from a queue.

        args and kwargs will be passed to Consumer constructor.
        Don't use future_to_notify - it's done here!

        Take care not to lose the Consumer object - it's the only way to cancel a consumer!

        .. note:: You don't need to explicitly declare queues and exchanges that you will be using beforehand,
                  this will do this for you on the same channel.

        If accepts more arguments. Consult :class:`coolamqp.attaches.consumer.Consumer` for details.

        :param queue: Queue object, being consumed from right now.
            Note that name of anonymous queue might change at any time!
        :param on_message: callable that will process incoming messages
                           if you leave it at None, messages will be .put into self.events
        :param span: optional span, if opentracing is installed
        :param dont_trace: if True, this won't output a span
        :param body_receive_mode: a :class:`coolamqp.attaches.consumer.BodyReceiveMode` to signal how to build the received
            `                     :class:`coolamqp.objects.ReceivedMessage`
        :return: a tuple (Consumer instance, and a Future), that tells, when consumer is ready
        """
        if span is not None and not dont_trace:
            child_span = self._make_span('consume', span)
        else:
            child_span = None
        fut = Future()
        fut.set_running_or_notify_cancel()  # it's running right now
        on_message = on_message or (
            lambda msg: self.events.put_nowait(MessageReceived(msg)))
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
                confirm=None,  # type: tp.Optional[bool]
                span=None,  # type: tp.Optional[opentracing.Span]
                dont_trace=False    # type: bool
                ):  # type: (...) -> tp.Optional[Future]
        """
        Publish a message.

        :param message: Message to publish
        :param exchange: exchange to use. Default is the "direct" empty-name exchange.
        :param routing_key: routing key to use
        :param confirm: Whether to publish it using confirms/transactions.
                        If you choose so, you will receive a Future that can be used
                        to check it broker took responsibility for this message.
                        Note that if confirm is False, and message cannot be delivered to broker at once,
                        it will be discarded
        :param span: optionally, current span, if opentracing is installed
        :param dont_trace: if set to True, a span won't be generated
        :return: Future to be finished on completion or None, is confirm was not chosen
        """
        if self.tracer is not None and not dont_trace:
            span = self._make_span('publish', span)

        if isinstance(exchange, Exchange):
            exchange = exchange.name.encode('utf8')
        elif exchange is None:
            exchange = b''
        elif isinstance(exchange, six.text_type):
            exchange = exchange.encode('utf8')

        if isinstance(routing_key, six.text_type):
            routing_key = routing_key.encode('utf8')

        try:
            if confirm:
                clb = self.pub_tr
            else:
                clb = self.pub_na
            return clb.publish(message, exchange, routing_key, span)
        except Publisher.UnusablePublisher:
            raise NotImplementedError(
                u'Sorry, this functionality is not yet implemented!')

    def start(self, wait=True, timeout=10.0):
        """
        Connect to broker. Initialize Cluster.

        Only after this call is Cluster usable.
        It is not safe to fork after this.

        :param wait: block until connection is ready. If None is given, then start will block as long as necessary.
        :type wait: bool
        :param timeout: timeout to wait until the connection is ready. If it is not, a
                        ConnectionDead error will be raised
        :type timeout: float | int | None
        :raise RuntimeError: called more than once
        :raise ConnectionDead: failed to connect within timeout
        """
        if self.started:
            raise RuntimeError(u'[%s] This was already called!' % (self.name,))
        self.started = True

        self.listener = ListenerThread(name=self.name)

        self.attache_group = AttacheGroup()

        self.events = six.moves.queue.Queue()  # for coolamqp.clustering.events.*

        self.snr = SingleNodeReconnector(self.node, self.attache_group,
                                         self.listener, self.extra_properties,
                                         self.log_frames, self.name)
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
            if timeout is None:
                while not self.connected:
                    time.sleep(0.2)
            else:
                while not self.connected and monotonic() - start_at < timeout:
                    time.sleep(0.1)
                if not self.connected:
                    raise ConnectionDead(
                        '[%s] Could not connect within %s seconds' % (self.name, timeout,))

    @property
    def properties(self):
        """
        Return a :class:`coolamqp.objects.ServerProperties` if a connection was established
        """
        return self.snr.properties

    def shutdown(self, wait=True):  # type: (bool) -> None
        """
        Terminate all connections, release resources - finish the job.

        :param wait: block until this is done
        :raise RuntimeError: if called without start() being called first
        """
        self.connected = False
        if not self.started:
            raise RuntimeError(u'shutdown without start')

        logger.info('[%s] Commencing shutdown', self.name)

        self.listener.terminate()
        if wait:
            self.listener.join()

    def is_shutdown(self):
        """
        :return: bool, if this was started and later disconnected.
        """
        return self.started and not self.connected
