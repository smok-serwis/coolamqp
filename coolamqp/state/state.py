# coding=UTF-8
from __future__ import absolute_import, division, print_function
import concurrent.futures


class BrokerState(object):
    """
    A state of the broker. List of messages to send (including their dispositions)
    and so on.
    """

    def __init__(self):

        # Transient messages - THESE WILL BE DROPPED ON THE FLOOR UPON A DISCONNECT
        self.messages_to_push = []  # list of (Message object, exchange_name, routing_key)

        # Messages to publish - THESE WILL NOT BE DROPPED ON THE FLOOR UPON A DC
        self.messages_to_tx = []    # list of (SendMessage object)

        # a list of (Queue instance, delivery_tag, auto_ack)
        self.queues_subscribed = []

