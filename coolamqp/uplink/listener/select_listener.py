# coding=UTF-8
from __future__ import absolute_import, division, print_function

import collections
import heapq
import itertools
import logging
import select

import monotonic

from coolamqp.uplink.listener.socket import SocketFailed, BaseSocket

logger = logging.getLogger(__name__)


class SelectSocket(BaseSocket):
    """
    SelectListener substitutes your BaseSockets with this
    """

    def __hash__(self):
        return self.sock.fileno().__hash__()

    def __init__(self, sock, on_read, on_fail, listener):
        BaseSocket.__init__(self, sock, on_read=on_read, on_fail=on_fail)
        self.listener = listener
        self.priority_queue = collections.deque()

    def send(self, data, priority=False):
        """
        This can actually get called not by ListenerThread.
        """
        BaseSocket.send(self, data, priority=priority)

    def oneshot(self, seconds_after, callable):
        """
        Set to fire a callable N seconds after
        :param seconds_after: seconds after this
        :param callable: callable/0
        """
        self.listener.oneshot(self, seconds_after, callable)

    def noshot(self):
        """
        Clear all time-delayed callables.

        This will make no time-delayed callables delivered if ran in listener thread
        """
        self.listener.noshot(self)


class SelectListener(object):
    """
    A listener using select.
    """

    def __init__(self):
        self.readable_sockets = set()
        self.writable_sockets = set()
        self.exception_sockets = set()
        self.fd_to_sock = {}
        self.time_events = []

    def wait(self, timeout=1):
        rd_socks, wd_socks, ex_socks = select.select(self.readable_sockets,
                                                     self.writable_sockets,
                                                     self.exception_sockets, timeout)

        # Timer events
        mono = monotonic.monotonic()
        while len(self.time_events) > 0 and (self.time_events[0][0] < mono):
            ts, fd, callback = heapq.heappop(self.time_events)
            callback()

        for readable_socket in rd_socks:
            try:
                readable_socket.on_read()
            except SocketFailed:
                self.readable_sockets.remove(readable_socket)
                self.exception_sockets.remove(readable_socket)
                try:
                    self.writable_sockets.remove(readable_socket)
                except KeyError:
                    pass
                readable_socket.on_fail()
                readable_socket.close()

        for exception_socket in ex_socks:
            exception_socket.on_fail()
            exception_socket.close()
            self.noshot(exception_socket)

        for writable_socket in itertools.chain(wd_socks, self.readable_sockets - set(self.writable_sockets)):
            a = writable_socket.on_write()
            if a and writable_socket in self.writable_sockets:
                # This socket is done sending data as for now
                self.writable_sockets.remove(writable_socket)
            if not a:
                self.writable_sockets.add(writable_socket)

        # Check if the socket wants to send anything more
        for readable_socket in self.readable_sockets:
            if len(readable_socket.data_to_send) > 0:
                self.writable_sockets.add(readable_socket)

    def noshot(self, sock):
        """
        Clear all one-shots for a socket
        :param sock: BaseSocket instance
        """
        fd = sock.fileno()
        self.time_events = [q for q in self.time_events if q[1] != fd]

    def shutdown(self):
        """
        Forcibly close all sockets that this manages (calling their on_fail's),
        and close the object.

        This object is unusable after this call.
        """
        self.time_events = []
        for sock in self.readable_sockets:
            sock.on_fail()
            sock.close()

        self.readable_sockets = set()
        self.writable_sockets = set()
        self.exception_sockets = set()

        self.fd_to_sock = {}

    def oneshot(self, sock, delta, callback):
        """
        A socket registers a time callback
        :param sock: BaseSocket instance
        :param delta: "this seconds after now"
        :param callback: callable/0
        """
        if sock.fileno() in self.fd_to_sock:
            heapq.heappush(self.time_events, (monotonic.monotonic() + delta,
                                              sock.fileno(),
                                              callback
                                              ))

    def register(self, sock, on_read=lambda data: None,
                 on_fail=lambda: None):
        """
        Add a socket to be listened for by the loop.

        :param sock: a socket instance (as returned by socket module)
        :param on_read: callable(data) to be called with received data
        :param on_fail: callable() to be called when socket fails

        :return: a BaseSocket instance to use instead of this socket
        """
        sock = SelectSocket(sock, on_read, on_fail, self)
        self.fd_to_sock[sock.fileno()] = sock

        self.readable_sockets.add(sock)
        self.exception_sockets.add(sock)
        return sock
