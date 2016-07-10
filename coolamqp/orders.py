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

    def completed(self):
        self._result = True
        self.lock.release()

        if self.on_completed is not None:
            self.on_completed()

    def failed(self, e):
        """
        :param e: AMQPError instance
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


class DeclareExchange(Order):
    """Declare an exchange"""
    def __init__(self, exchange, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.exchange = exchange


class DeleteExchange(Order):
    """Delete an exchange"""
    def __init__(self, exchange, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.exchange = exchange


class DeclareQueue(Order):
    """Declare a a queue"""
    def __init__(self, queue, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.queue = queue


class ConsumeQueue(Order):
    """Declare and consume from a queue"""
    def __init__(self, queue, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.queue = queue


class DeleteQueue(Order):
    """Delete a queue"""
    def __init__(self, queue, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.queue = queue


class SetQoS(Order):
    """Set QoS"""
    def __init__(self, prefetch_window, prefetch_count, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.qos = (prefetch_window, prefetch_count)


class CancelQueue(Order):
    """Cancel consuming from a queue"""
    def __init__(self, queue, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.queue = queue


class AcknowledgeMessage(Order):
    """ACK a message"""
    def __init__(self, connect_id, delivery_tag, on_completed):
        Order.__init__(self, on_completed=on_completed)
        self.connect_id = connect_id
        self.delivery_tag = delivery_tag


class NAcknowledgeMessage(Order):
    """NACK a message"""
    def __init__(self, connect_id, delivery_tag, on_completed):
        Order.__init__(self, on_completed=on_completed)
        self.connect_id = connect_id
        self.delivery_tag = delivery_tag
