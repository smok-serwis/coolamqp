# coding=UTF-8
from __future__ import absolute_import, division, print_function
import six
import logging
import select
import monotonic
import heapq

from coolamqp.uplink.listener.socket import SocketFailed, BaseSocket


logger = logging.getLogger(__name__)


class EpollSocket(BaseSocket):
    """
    EpollListener substitutes your BaseSockets with this
    """
    def __init__(self, sock, on_read, on_fail, listener):
        BaseSocket.__init__(self, sock, on_read=on_read, on_fail=on_fail)
        self.listener = listener

    def get_epoll_eventset(self):
        if len(self.data_to_send) > 0:
            return select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP | select.EPOLLOUT
        else:
            return select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP

    def send(self, data):
        self.data_to_send.append(data)
        self.listener.epoll.modify(self, self.get_epoll_eventset())

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


class EpollListener(object):
    """
    A listener using epoll.
    """

    def __init__(self):
        self.epoll = select.epoll()
        self.fd_to_sock = {}
        self.time_events = []

    def wait(self, timeout=1):
        events = self.epoll.poll(timeout=timeout)
        for fd, event in events:
            sock = self.fd_to_sock[fd]

            # Errors
            try:
                if event & (select.EPOLLERR | select.EPOLLHUP):
                    raise SocketFailed()
                elif event & select.EPOLLIN:
                    sock.on_read()
                elif event & select.EPOLLOUT:
                    sock.on_write()
            except SocketFailed:
                self.epoll.unregister(fd)
                del self.fd_to_sock[fd]
                sock.on_fail()
                self.noshot(sock)
                sock.close()
            else:
                self.epoll.modify(fd, sock.get_epoll_eventset())

        # Timer events
        while len(self.time_events) > 0 and (self.time_events[0][0] < monotonic.monotonic()):
            ts, fd, callback = heapq.heappop(self.time_events)
            callback()

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
        for sock in six.itervalues(self.fd_to_sock):
            sock.on_fail()
            sock.close()
        self.fd_to_sock = {}
        self.epoll.close()
        self.time_events = []

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
        sock = EpollSocket(sock, on_read, on_fail, self)
        self.fd_to_sock[sock.fileno()] = sock

        self.epoll.register(sock, sock.get_epoll_eventset())
        return sock

