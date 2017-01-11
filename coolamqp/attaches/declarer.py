# coding=UTF-8
"""
queue.declare, exchange.declare and that shit
"""
from __future__ import print_function, absolute_import, division
import six
import collections
import logging
from coolamqp.framing.definitions import ChannelOpenOk, ExchangeDeclare, ExchangeDeclareOk, QueueDeclare, \
                                        QueueDeclareOk, ChannelClose
from coolamqp.attaches.channeler import Channeler, ST_ONLINE, ST_OFFLINE
from coolamqp.uplink import PUBLISHER_CONFIRMS, MethodWatch, FailWatch
from coolamqp.attaches.utils import AtomicTagger, FutureConfirmableRejectable, Synchronized

from coolamqp.objects import Future, Exchange, Queue, Callable
from coolamqp.exceptions import AMQPError, ConnectionDead

logger = logging.getLogger(__name__)



class Operation(object):
    """
    Represents the op currently carried out.

    This will register it's own callback. Please, call on_connection_dead when connection is broken
    to fail futures with ConnectionDead, since this object does not watch for Fails
    """
    def __init__(self, declarer, obj, fut=None):
        self.done = False
        self.fut = fut
        self.declarer = declarer
        self.obj = obj

        self.on_done = Callable()   # callable/0

    def on_connection_dead(self):
        """To be called by declarer when our link fails"""
        if self.fut is not None:
            self.fut.set_exception(ConnectionDead())
            self.fut = None

    def perform(self):
        """Attempt to perform this op."""
        obj = self.obj
        if isinstance(obj, Exchange):
            self.method_and_watch(ExchangeDeclare(self.obj.name.encode('utf8'), obj.type, False, obj.durable,
                                                  obj.auto_delete, False, False, []),
                                  (ExchangeDeclareOk, ChannelClose),
                                  self._declared)
        elif isinstance(obj, Queue):
            self.method_and_watch(QueueDeclare(obj.name, False, obj.durable, obj.exclusive, obj.auto_delete, False, []),
                                  (QueueDeclareOk, ChannelClose),
                                  self._declared)

    def _callback(self, payload):
        if isinstance(payload, ChannelClose):
            if self.fut is not None:
                self.fut.set_exception(AMQPError(payload))
                self.fut = None
        else:
            if self.fut is not None:
                self.fut.set_result()
                self.fut = None



class Declarer(Channeler, Synchronized):
    """
    Doing other things, such as declaring, deleting and other stuff.

    This also maintains a list of declared queues/exchanges, and redeclares them on each reconnect.
    """
    def __init__(self):
        """
        Create a new declarer.
        """
        Channeler.__init__(self)
        Synchronized.__init__(self)

        self.declared = set()   # since Queues and Exchanges are hashable...
                                # anonymous queues aren't, but we reject those
                                # persistent

        self.left_to_declare = collections.deque()  # since last disconnect. persistent+transient
                                                    # deque of Operation objects

        self.on_discard = Callable()    # callable/1, with discarded elements

        self.doing_now = None   # Operation instance that is being progressed right now

    @Synchronized.synchronized
    def attach(self, connection):
        Channeler.attach(self, connection)
        connection.watch(FailWatch(self.on_fail))

    @Synchronized.synchronized
    def on_fail(self):
        self.state = ST_OFFLINE

        # fail all operations in queue...
        while len(self.left_to_declare) > 0:
            self.left_to_declare.pop().on_connection_dead()

        if self.now_future is not None:
            # we were processing something...
            self.now_future.set_exception(ConnectionDead())
            self.now_future = None
            self.now_processed = None



    def on_close(self, payload=None):
        old_con = self.connection
        super(Declarer, self).on_close(payload=payload)

        # But, we are super optimists. If we are not cancelled, and connection is ok,
        # we must reestablish
        if old_con.state == ST_ONLINE and not self.cancelled:
            self.attach(old_con)

        if payload is None:
            # Oh, it's pretty bad. We will need to redeclare...
            for obj in self.declared:
                self.left_to_declare


    def declare(self, obj, persistent=False):
        """
        Schedule to have an object declared.

        Future is returned, so that user knows when it happens.

        Declaring is not fast, because there is at most one declare at wire, but at least we know WHAT failed.
        Declaring same thing twice is a no-op.

        Note that if re-declaring these fails, they will be silently discarded.
        You can subscribe an on_discard(Exchange | Queue) here.

        :param obj: Exchange or Queue instance
        :param persistent: will be redeclared upon disconnect. To remove, use "undeclare"
        :return: a Future instance
        :raise ValueError: tried to declare anonymous queue
        """

        if isinstance(obj, Queue):
            if obj.anonymous:
                raise ValueError('Cannot declare anonymous queue')

        if obj in self.declared:
            return

        fut = Future()

        if persistent:
            self.declared.add(obj)

        op = Operation(self, obj, fut)

        self.left_to_declare.append(op)

        if self.state == ST_ONLINE:
            self._do_operations()

        return fut


    @Synchronized.synchronized
    def _do_operations(self):
        """Attempt to do something"""
        if len(self.left_to_declare) == 0 or self.busy:
            return
        else:
            self.now_processed, self.now_future = self.left_to_declare.popleft()
        self.busy = True


    def on_setup(self, payload):

        if isinstance(payload, ChannelOpenOk):
            self.busy = False
            self._do_operations()
