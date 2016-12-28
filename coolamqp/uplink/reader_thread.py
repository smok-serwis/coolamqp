# coding=UTF-8
from __future__ import absolute_import, division, print_function
import socket
import threading


class ReaderThread(threading.Thread):
    """
    A thread, whose job is to receive AMQP framing from AMQP TCP socket.

    Thread may inform Uplink of socket's lossage via on_socket_failed(exception). It should exit afterwards at once.
    """

    def __init__(self, sock, on_failure):
        """
        :param uplink: Uplink instance
        :param sock: a socket to use
        """
        threading.Thread.__init__(self)
        self.daemon = True

        self.uplink = uplink
        self.sock = sock
        self.is_cancelled = False


    def on_cancel(self):
        """
        Called by Uplink when it decides that we should not report any more framing, and should just die.
        """
        self.is_cancelled = True


    def run(self):_