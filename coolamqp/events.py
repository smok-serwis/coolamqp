# coding=UTF-8
"""
Events emitted by Cluster
"""


class ClusterEvent(object):
    """Base class for events emitted by cluster"""


class ConnectionDown(ClusterEvent):
    """Connection to broker has been broken"""


class ConnectionUp(ClusterEvent):
    """Connection to broker has been (re)established"""

    def __init__(self, initial=False):
        self.initial = initial  #: public, is this first connection up in this cluster ever?


class MessageReceived(ClusterEvent):
    """A message has been received from the broker"""
    def __init__(self, message):
        """
        :param message: ReceivedMessage instance
        """
        self.message = message


class ConsumerCancelled(ClusterEvent):
    """
    Broker cancelled a consumer of ours.
    This is also generated in response to cancelling consumption from a queue
    """

    BROKER_CANCEL = 0
    REFUSED_ON_RECONNECT = 1
    USER_CANCEL = 2

    def __init__(self, queue, reason):
        """
        :param queue: Queue whose consumer was cancelled
        :param reason: Reason why the consumer was cancelled
            ConsumerCancelled.BROKER_CANCEL - broker informed us about cancelling
            ConsumerCancelled.REFUSED_ON_RECONNECT - during a reconnect, I tried to consume an exclusive
                                                     queue and got ACCESS_REFUSED.
                                                     These messages will arrive between ConnectionDown and
                                                     ConnectionUp.
            ConsumedCancelled.USER_CANCEL - user called cluster.cancel()
        """
        self.queue = queue
        self.reason = reason
