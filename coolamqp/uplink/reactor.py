# coding=UTF-8
from __future__ import absolute_import, division, print_function



class Reactor(object):
    """
    Base class for objects that can:
    - Receive AMQPFrame's
    - Send AMQPFrame's
    - Receive information about termination of connection

    Default implementation is a no-op default reactor.
    """
    def __init__(self):
        self.send_frame = lambda frame: None


    def on_frame(self, frame):
        """
        Frame was received.
        :param frame: AMQPFrame instance
        """

    def set_send_frame(self, sender):
        """
        Called when Reactor is registered in a Connection
        :param sender: callable(amqp_frame) to call if Reactor wants to send a frame
        """
        self.send_frame = sender

    def on_close(self):
        """
        Called when connection is closed
        """
