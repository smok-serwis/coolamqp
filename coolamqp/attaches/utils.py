# coding=UTF-8
from __future__ import print_function, absolute_import, division

import functools
import logging
import threading

logger = logging.getLogger(__name__)


class ConfirmableRejectable(object):
    """
    Protocol for objects put into AtomicTagger. You need not subclass it,
    just support this protocol.
    """
    __slots__ = ()

    def confirm(self):  # type: () -> None
        """
        This has been ACK'd
        :return: don't care
        """

    def reject(self):  # type: () -> None
        """
        This has been REJECT'd/NACK'd
        :return: don't care
        """


class FutureConfirmableRejectable(ConfirmableRejectable):
    """
    A ConfirmableRejectable that can result a future (with None),
    or Exception it with a message
    """
    __slots__ = ('future', )

    def __init__(self, future):  # type: (concurrent.futures.Future) -> None
        self.future = future

    def confirm(self):  # type: () -> None
        self.future.set_result(None)

    def reject(self):  # type: () -> None
        self.future.set_exception(Exception())


class AtomicTagger(object):
    """
    This implements a thread-safe dictionary of (integer=>ConfirmableRejectable | None),
    used for processing delivery tags / (negative) acknowledgements.
        - you can requisition a key. This key belongs only to you, and the whole world
          doesn't know you have it.

            delivery_tag_to_use = tagger.get_key()

        - you can deposit a ConfirmableRejectable into the  tagger.

            tagger.deposit(delivery_tag, message)

         After you do so, this tag is subject to be acked/nacked. Read on.

        - you can (multiple)(ack/nack) messages. This coresponds to multiple bit
          used in basic.ack/basic.nack.

          If this is done, your message objects (that MUST implement the
          ConfirmableRejectable protocol) will have respective methods called.
          These methods MUST NOT depend on particular state of locking by this
          object.

    Thread safety is implemented using reentrant locking. The lock object is a
    threading.RLock, and you can access it at atomicTagger.lock.

    Please note that delivery tags are increasing non-negative integer.
    Therefore, X>Y implies that sending/receiving X happened after Y.

    Note that key/delivery_tag of 0 has special meaning of "everything so far".

    This has to be fast for most common cases. Corner cases will be resolved correctly,
    but maybe not fast.
    """
    __slots__ = ('lock', 'next_tag', 'tags')

    def __init__(self):
        self.lock = threading.RLock()

        # Protected by lock
        self.next_tag = 1  # 0 is AMQP-reserved to mean "everything so far"
        self.tags = []  # a list of (tag, ConfirmableRejectable)
        # they remain to be acked/nacked
        # invariant: FOR EACH i, j: (i>j) => (tags[i][0] > tags[j][0])

    def deposit(self, tag, obj):
        """
        Put a tag into the tag list.

        Putting the same tag more than one time will result in undefined behaviour.

        :param tag: non-negative integer
        :param obj: ConfirmableRejectable
                    if you put something that isn't a ConfirmableRejectable, you won't get bitten
                    until you call .ack() or .nack().
        """
        assert tag >= 0
        opt = (tag, obj)

        with self.lock:
            if len(self.tags) == 0:
                self.tags.append(opt)
            elif self.tags[-1][0] < tag:
                self.tags.append(opt)
            else:
                # Insert a value at place where it makes sense. Iterate from the end, because
                # values will usually land there...
                i = len(self.tags) - 1  # start index

                while i > 0:  # this will terminate at i=0
                    if self.tags[i][
                        0] > tag:  # this means we should insert it here...
                        break
                    i -= 1  # previousl index

                self.tags.insert(i, opt)

    def __acknack(self, tag, multiple, ack):
        """
        :param tag: Note that 0 means "everything"
        :param ack: True to ack, False to nack
        """
        # Compute limits - they go from 0 to somewhere
        with self.lock:
            start = 0
            # start and stop will signify the PYTHON SLICE parameters

            if tag > 0:

                if multiple:
                    # Compute the ranges
                    for stop, opt in enumerate(self.tags):
                        if opt[0] == tag:
                            stop += 1  # this is exactly this tag. Adjust stop to end one further (Python slicing) and stop
                            break
                        if opt[0] > tag:
                            break  # We went too far, but it's OK, we don't need to bother with adjusting stop
                    else:
                        # List finished without breaking? That would mean the entire range!
                        stop = len(self.tags)
                else:
                    # Just find that piece
                    for index, opt in enumerate(self.tags):
                        if opt[0] == tag:
                            stop = index + 1
                            break
                    else:
                        return  # not found!

                if not multiple:
                    start = stop - 1
            else:
                # Oh, I know the range!
                stop = len(self.tags)

            items = self.tags[start:stop]
            del self.tags[start:stop]

        for tag, cr in items:
            if ack:
                cr.confirm()
            else:
                cr.reject()

    def ack(self, tag, multiple):
        """
        Acknowledge given objects.

        If multiple, objects UP TO AND INCLUDING tag will have .confirm() called.
        If it's false, only this precise objects will have done so.
        It this object does not exist, nothing will happen. Acking same tag more than one time
        is a no-op.

        Things acked/nacked will be evicted from .data
        :param tag: delivery tag to use. Note that 0 means "everything so far"
        """
        self.__acknack(tag, multiple, True)

    def nack(self, tag, multiple):
        """
        Acknowledge given objects.

        If multiple, objects UP TO AND INCLUDING tag will have .confirm() called.
        If it's false, only this precise objects will have done so.
        It this object does not exist, nothing will happen. Acking same tag more than one time
        is a no-op.

        Things acked/nacked will be evicted from .data
        :param tag: delivery tag to use. Note that 0 means "everything so far"
        """
        self.__acknack(tag, multiple, False)

    def get_key(self):
        """
        Return a key. It won't be seen here until you deposit it.

        It's just yours, and you can do whatever you want with it, even drop on the floor.
        :return: a positive integer
        """
        with self.lock:
            self.next_tag += 1
            return self.next_tag - 1


class Synchronized(object):
    """
    I have a lock and can sync on it. Use like:

    class Synced(Synchronized):

        @synchronized
        def mandatorily_a_instance_method(self, ...):
            ...

    """

    def __init__(self):
        self._monitor_lock = threading.Lock()

    def get_monitor_lock(self):
        return self._monitor_lock

    @staticmethod
    def synchronized(fun):
        @functools.wraps(fun)
        def monitored(*args, **kwargs):
            with args[0]._monitor_lock:
                return fun(*args, **kwargs)

        return monitored
