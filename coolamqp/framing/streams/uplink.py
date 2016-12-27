# coding=UTF-8
from __future__ import absolute_import, division, print_function
import collections
import socket

class Uplink(object):
    """
    This coordinates access to a shared socket.

    This should be discarded when the TCP connection dies.
    """

    def __init__(self, sock):
        """
        Pass a fresh socket, just a
        :param sock:
        """
        self.sock = sock
        self.sock.settimeout(0)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)  # disable Nagle

        # when a method frame comes in, it is checked here first.
        # if there's a match, that means a sync request completed.
        self.waiting_queue = collections.defaultdict()



