# coding=UTF-8
"""
Orders that can be dispatched to ClusterHandlerThread
"""
from threading import Lock
import warnings


_NOOP_COMP = lambda: None
_NOOP_FAIL = lambda e: None


class Order(object):
    """Base class for orders dispatched to ClusterHandlerThread"""
    def __init__(self, on_completed=None, on_failed=None):
        """
        Please note that callbacks will be executed BEFORE the lock is released,
        but after .result is updated, ie. if
        you have something like

            amqp.send(.., on_completed=hello).result()
            bye()

        then hello() will be called BEFORE bye().
        Callbacks are called from CoolAMQP's internal thread.

        If this fails, then property .error_code can be read to get the error code.
        and .reply_text has the reply of the server or some other reason. These are set before
        callbacks are called.

        Error code is None, if not available, or AMQP constants describing errors,
        eg. 502 for syntax error.

        A discarded or cancelled order is considered FAILED
        """
        self.on_completed = on_completed or _NOOP_COMP
        self.on_failed = on_failed or _NOOP_FAIL
        self._result = None  # None on non-completed
                            # True on completed OK
                            # exception instance on failed
                            # private
        self.lock = Lock()
        self.lock.acquire()
        self.cancelled = False          #: public
        self.discarded = False          #: public
        self.error_code = None
        self.reply_text = None

    def has_finished(self):
        """Return if this task has either completed or failed"""
        return self._result is not None

    def cancel(self):
        """Cancel this order"""
        self.cancelled = True

    def _completed(self):       # called by handler
        self._result = True
        self.on_completed()
        self.lock.release()

    def _discard(self):     # called by handler
        from coolamqp.backends.base import Discarded
        self.discarded = True
        self.on_failed(Discarded())
        self.lock.release()

    def _failed(self, e):       # called by handler
        """
        :param e: AMQPError instance or Cancelled instance
        """
        from coolamqp.backends import Cancelled
        self._result = e
        if not isinstance(e, Cancelled):    # a true error
            self.error_code = e.code
            self.reply_text = e.reply_text

        self.on_failed(e)
        self.lock.release()

    def wait(self):
        """Wait until this is completed and return whether the order succeeded"""
        self.lock.acquire()
        return self._result is True

    def has_failed(self):
        """Return whether the operation failed, ie. completed but with an error code.
        Cancelled and discarded ops are considered failed.
        This assumes that this order has been .wait()ed upon"""
        return self._result is not True

    def result(self):
        """Wait until this is completed and return a response"""
        warnings.warn('Use .wait() instead', PendingDeprecationWarning)
        self.lock.acquire()
        return self._result

    @staticmethod
    def _discarded(on_completed=None, on_failed=None):   # return order for a discarded message
        o = Order(on_completed=on_completed, on_failed=on_failed)
        self.on_completed()


class SendMessage(Order):
    """Send a message"""
    def __init__(self, message, exchange, routing_key, discard_on_fail=False, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.message = message
        self.exchange = exchange
        self.discard_on_fail = discard_on_fail
        self.routing_key = routing_key


class _Exchange(Order):
    """Things with exchanges"""
    def __init__(self, exchange, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.exchange = exchange


class DeclareExchange(_Exchange):
    """Declare an exchange"""


class DeleteExchange(_Exchange):
    """Delete an exchange"""


class _Queue(Order):
    """Things with queues"""
    def __init__(self, queue, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.queue = queue


class DeclareQueue(_Queue):
    """Declare a a queue"""


class ConsumeQueue(_Queue):
    """Declare and consume from a queue"""
    def __init__(self, queue, no_ack=False, on_completed=None, on_failed=None):
        _Queue.__init__(self, queue, on_completed=on_completed, on_failed=on_failed)
        self.no_ack = no_ack


class DeleteQueue(_Queue):
    """Delete a queue"""


class CancelQueue(_Queue):
    """Cancel consuming from a queue"""


class SetQoS(Order):
    """Set QoS"""
    def __init__(self, prefetch_window, prefetch_count, global_, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.qos = prefetch_window, prefetch_count, global_
1

class _AcksAndNacks(Order):
    """related to acking and nacking"""
    def __init__(self, connect_id, delivery_tag, on_completed):
        Order.__init__(self, on_completed=on_completed)
        self.connect_id = connect_id
        self.delivery_tag = delivery_tag


class AcknowledgeMessage(_AcksAndNacks):
    """ACK a message"""


class NAcknowledgeMessage(_AcksAndNacks):
    """NACK a message"""
