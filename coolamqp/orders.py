"""
Orders that can be dispatched to ClusterHandlerThread
"""

class Order(object):
    """Base class for orders dispatched to ClusterHandlerThread"""
    def __init__(self, on_completed=None, on_failed=None):
        self.on_completed = on_completed
        self.on_failed = on_failed

    def completed(self):
        if self.on_completed is not None:
            self.on_completed()

    def failed(self, e):
        """
        :param e: AMQPError instance
        """
        if self.on_failed is not None:
            self.on_failed(e)


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

class ConsumeQueue(Order):
    """Declare and consume from a queue"""
    def __init__(self, queue, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.queue = queue

class CancelQueue(Order):
    """Cancel consuming from a queue"""
    def __init__(self, queue, on_completed=None, on_failed=None):
        Order.__init__(self, on_completed=on_completed, on_failed=on_failed)
        self.queue = queue
