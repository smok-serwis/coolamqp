# coding=UTF-8
from __future__ import absolute_import, division, print_function

import collections
import heapq
import logging
import select
import socket

import monotonic
import six

from coolamqp.uplink.listener.socket import SocketFailed, BaseSocket

logger = logging.getLogger(__name__)

RO = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
RW = RO | select.EPOLLOUT


class SelectSocket(BaseSocket):
    """
    EpollListener substitutes your BaseSockets with this
    :type sock: socket.socket
    :type on_read: tp.Callable[[bytes], None]
    :type on_fail: tp.Callable[[], None]
    :type listener: coolamqp.uplink.listener.ListenerThread
    """

    def __init__(self, sock, on_read, on_fail, listener):
        BaseSocket.__init__(self, sock, on_read=on_read, on_fail=on_fail)
        self.listener = listener

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
    A listener using select
    """

    def __init__(self):
        self.fd_to_sock = {}
        self.time_events = []
        self.sockets_to_activate = []

    def close_socket(self, sock):  # type: (BaseSocket) -> None
        file_no = sock.fileno()
        sock.on_fail()
        self.noshot(sock)
        sock.close()
        del self.fd_to_sock[file_no]

    def wait(self, timeout=1):
        for socket_to_activate in self.sockets_to_activate:
            logger.debug('Activating fd %s', (socket_to_activate.fileno(),))
            self.fd_to_sock[socket_to_activate.fileno()] = socket_to_activate
        self.sockets_to_activate = []

        rds_and_exs = []        # waiting both for read and for exception
        wrs = []                # waiting for write
        for sock in six.itervalues(self.sockets_to_activate.values()):
            rds_and_exs.append(sock)
            if sock.wants_to_send_data():
                wrs.append(sock)

        try:
            rds, wrs, exs = select.select(rds_and_exs, wrs, rds_and_exs, timeout=timeout)
        except select.error:
            for sock in rds_and_exs:
                try:
                    select.select([sock], [], [], timeout=0)
                except select.error:
                    self.close_socket(sock)
                    return
            else:
                return

        for sock_rd in rds:
            try:
                sock_rd.on_read()
            except SocketFailed:
                return self.close_socket(sock_rd)

        for sock_wr in wrs:
            try:
                sock_wr.on_write()
            except SocketFailed:
                return self.close_socket(sock_wr)

        for sock_ex in exs:
            try:
                sock_rd.on_read()
            except SocketFailed:
                return self.close_socket(sock_ex)

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
        for sock in list(six.itervalues(self.fd_to_sock)):
            sock.on_fail()
            sock.close()

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
        self.sockets_to_activate.append(sock)
        return sock
