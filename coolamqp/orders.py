#coding=UTF-8
"""
Orders that can be dispatched to ClusterHandlerThread
"""
from threading import Lock


class Order(object):
    """Base class for orders dispatched to ClusterHandlerThread"""
    def __init__(self, on_completed=None, on_failed=None):
        self.on_completed = on_completed
        self.on_failed = on_failed
        self._result = None  # None on non-completed
                            # True on completed OK
                            # exception instance on failed
        self.lock = Lock()
        self.lock.acquire()
        self.cancelled = False

    def has_finished(self):
        """Return if this task has either completed or failed"""
        return self._result is not None

    def cancel(self):
        """Cancel this order"""
        self.cancelled = True

    def completed(self):
        self._result = True
        self.lock.release()

        if self.on_completed is not None:
            self.on_completed()

    def failed(self, e):
        """
        :param e: AMQPError instance or Cancelled instance
        """
        self._result = e
        self.lock.release()

        if self.on_failed is not None:
            self.on_failed(e)

    def result(self):
        """Wait until this is completed and return a response"""
        self.lock.acquire()
        return self._result


class SendMessage(Order):
    """Send a message"""
    def __init__(self, message, exchange, routing_key, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.message = message
        self.exchange = exchange
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

class DeleteQueue(_Queue):
    """Delete a queue"""

class CancelQueue(_Queue):
    """Cancel consuming from a queue"""


class SetQoS(Order):
    """Set QoS"""
    def __init__(self, prefetch_window, prefetch_count, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.qos = (prefetch_window, prefetch_count)


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
