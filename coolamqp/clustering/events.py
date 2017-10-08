# coding=UTF-8
"""
Cluster will emit Events.

They mean that something, like, happened.
"""
from __future__ import print_function, absolute_import, division

import logging

from coolamqp.objects import ReceivedMessage

logger = logging.getLogger(__name__)


class Event(object):
    """
    An event emitted by Cluster
    """


class NothingMuch(Event):
    """Nothing happened :D"""


class ConnectionLost(Event):
    """
    We have lost the connection.

    NOTE that we don't have a ConnectionUp, since re-establishing a connection
    is a complicated process. Broker might not have recognized the failure,
    and some queues will be blocked, some might be ok, and the state
    might be just a bit noisy.

    Please examine your Consumer's .state's to check whether link was regained
    """


class MessageReceived(ReceivedMessage, Event):
    """
    Something that works as an ersatz ReceivedMessage, but is an event
    """

    def __init__(self, msg):
        """:type msg: ReceivedMessage"""
        ReceivedMessage.__init__(self, msg.body, msg.exchange_name,
                                 msg.routing_key,
                                 properties=msg.properties,
                                 delivery_tag=msg.delivery_tag,
                                 ack=msg.ack, nack=msg.nack)
