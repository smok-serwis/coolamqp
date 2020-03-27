# coding=UTF-8
"""
queue.declare, exchange.declare and that shit
"""
from __future__ import print_function, absolute_import, division

import collections
import logging
from concurrent.futures import Future

from coolamqp.attaches.channeler import Channeler, ST_ONLINE
from coolamqp.attaches.utils import Synchronized
from coolamqp.exceptions import AMQPError, ConnectionDead
from coolamqp.framing.definitions import ChannelOpenOk, ExchangeDeclare, \
    ExchangeDeclareOk, QueueDeclare, \
    QueueDeclareOk, ChannelClose, QueueDelete, QueueDeleteOk
from coolamqp.objects import Exchange, Queue, Callable

logger = logging.getLogger(__name__)


class Operation(object):
    """
    An abstract operation.

    This class possesses the means to carry itself out and report back status.
    Represents the op currently carried out.

    This will register it's own callback. Please, call on_connection_dead when connection is broken
    to fail futures with ConnectionDead, since this object does not watch for Fails
    """
    __slots__ = ('done', 'fut', 'declarer', 'obj', 'on_done')

    def __init__(self, declarer, obj, fut=None):
        self.done = False
        self.fut = fut
        self.declarer = declarer
        self.obj = obj

        self.on_done = Callable()  # callable/0

    def on_connection_dead(self):
        """To be called by declarer when our link fails"""
        if self.fut is not None:
            self.fut.set_exception(ConnectionDead())
            self.fut = None

    def perform(self):
        """Attempt to perform this op."""
        obj = self.obj
        if isinstance(obj, Exchange):
            self.declarer.method_and_watch(
                ExchangeDeclare(self.obj.name.encode('utf8'), obj.type, False,
                                obj.durable,
                                obj.auto_delete, False, False, []),
                (ExchangeDeclareOk, ChannelClose),
                self._callback)
        elif isinstance(obj, Queue):
            self.declarer.method_and_watch(
                QueueDeclare(obj.name, False, obj.durable, obj.exclusive,
                             obj.auto_delete, False, []),
                (QueueDeclareOk, ChannelClose),
                self._callback)

    def _callback(self, payload):
        assert not self.done
        self.done = True
        if isinstance(payload, ChannelClose):
            if self.fut is not None:
                self.fut.set_exception(AMQPError(payload))
                self.fut = None
            else:
                # something that had no Future failed. Is it in declared?
                if self.obj in self.declarer.declared:
                    self.declarer.declared.remove(
                        self.obj)  # todo access not threadsafe
                    self.declarer.on_discard(self.obj)
        else:
            if self.fut is not None:
                self.fut.set_result(None)
                self.fut = None
        self.declarer.on_operation_done()


class DeleteQueue(Operation):
    def __init__(self, declarer, queue, fut):
        super(DeleteQueue, self).__init__(declarer, queue, fut=fut)

    def perform(self):
        queue = self.obj

        self.declarer.method_and_watch(
            QueueDelete(queue.name, False, False, False),
            (QueueDeleteOk, ChannelClose),
            self._callback)

    def _callback(self, payload):
        assert not self.done
        self.done = True
        if isinstance(payload, ChannelClose):
            self.fut.set_exception(AMQPError(payload))
        else:  # Queue.DeleteOk
            self.fut.set_result(None)
        self.declarer.on_operation_done()


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

        self.declared = set()  # since Queues and Exchanges are hashable...
        # anonymous queues aren't, but we reject those
        # persistent

        self.left_to_declare = collections.deque()  # since last disconnect. persistent+transient
        # deque of Operation objects

        self.on_discard = Callable()  # callable/1, with discarded elements

        self.in_process = None  # Operation instance that is being progressed right now

    def on_close(self, payload=None):

        # we are interested in ChannelClose during order execution,
        # because that means that operation was illegal, and must
        # be discarded/exceptioned on future

        if payload is None:

            if self.in_process is not None:
                self.in_process.on_connection_dead()
                self.in_process = None

            # connection down, panic mode engaged.
            while len(self.left_to_declare) > 0:
                self.left_to_declare.pop().on_connection_dead()

            # recast current declarations as new operations
            for dec in self.declared:
                self.left_to_declare.append(Operation(self, dec))

            super(Declarer, self).on_close()
            return

        elif isinstance(payload, ChannelClose):
            # Looks like a soft fail - we may try to survive that
            old_con = self.connection
            super(Declarer, self).on_close()

            # But, we are super optimists. If we are not cancelled, and connection is ok,
            # we must reestablish
            if old_con.state == ST_ONLINE and not self.cancelled:
                self.attach(old_con)
        else:
            super(Declarer, self).on_close(payload)

    def on_operation_done(self):
        """
        Called by operation, when it's complete (whether success or fail).
        Not called when operation fails due to DC
        """
        self.in_process = None
        self._do_operations()

    def delete_queue(self, queue):
        """
        Delete a queue.

        Future is returned, so that user knows when it happens. This may fail.
        Returned Future is already running, and so cannot be cancelled.

        If the queue is in declared consumer list, it will not be removed.

        :param queue: Queue instance
        :return: a Future
        """
        fut = Future()
        fut.set_running_or_notify_cancel()

        self.left_to_declare.append(DeleteQueue(self, queue, fut))
        self._do_operations()

        return fut

    def declare(self, obj, persistent=False):
        """
        Schedule to have an object declared.

        Future is returned, so that user knows when it happens.
        Returned Future is already running, and so cannot be cancelled.

        Exchange declarations never fail.
            Of course they do, but you will be told that it succeeded. This is by design,
            and due to how AMQP works.

        Queue declarations CAN fail.

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

        fut = Future()
        fut.set_running_or_notify_cancel()

        if persistent:
            if obj not in self.declared:
                self.declared.add(obj)  # todo access not threadsafe

        self.left_to_declare.append(Operation(self, obj, fut))
        self._do_operations()

        return fut

    @Synchronized.synchronized
    def _do_operations(self):
        """
        Attempt to execute something.

        To be called when it's possible that something can be done
        """
        if (self.state != ST_ONLINE) or len(self.left_to_declare) == 0 or (
                    self.in_process is not None):
            return

        self.in_process = self.left_to_declare.popleft()
        self.in_process.perform()

    def on_setup(self, payload):
        if isinstance(payload, ChannelOpenOk):
            assert self.in_process is None
            self.state = ST_ONLINE
            self._do_operations()
