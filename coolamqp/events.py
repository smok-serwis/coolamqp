"""
Events emitted by Cluster
"""


class ClusterEvent(object):
    """Base class for events emitted by cluster"""


class ConnectionDown(ClusterEvent):
    """Connection to broker has been broken"""


class ConnectionUp(ClusterEvent):
    """Connection to broker has been (re)established"""


class MessageReceived(ClusterEvent):
    """A message has been received from the broker"""
    def __init__(self, message):
        """
        :param message: ReceivedMessage instance
        """
        self.message = message


class ConsumerCancelled(ClusterEvent):
    """Broker cancelled a consumer of ours.
    This is also generated in response to cancelling consumption from a queue"""
    def __init__(self, queue):
        """
        :param queue: Queue whose consumer was cancelled
        """
        self.queue = queue
