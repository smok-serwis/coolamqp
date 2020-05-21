# coding=UTF-8
from __future__ import absolute_import, division, print_function

import logging
import select
import socket
import threading

import six

from coolamqp.uplink.listener.socket import SocketFailed, BaseSocket
from coolamqp.uplink.listener.base_listener import BaseListener


logger = logging.getLogger(__name__)

RO = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
RW = RO | select.EPOLLOUT


class EpollSocket(BaseSocket):

    def send(self, data, priority=False):
        """
        This can actually get called not by ListenerThread.
        """
        BaseSocket.send(self, data, priority=priority)
        try:
            self.listener.epoll.modify(self, RW)
        except socket.error:
            # silence. If there are errors, it's gonna get nuked soon.
            pass


class EpollListener(BaseListener):
    """
    A listener using epoll.
    """

    def __init__(self):
        self.epoll = select.epoll()
        self.socket_activation_lock = threading.Lock()
        self.sockets_to_activate = []
        super(EpollListener, self).__init__()

    def wait(self, timeout=1):
        with self.socket_activation_lock:
            for socket_to_activate in self.sockets_to_activate:
                logger.debug('Activating fd %s', (socket_to_activate.fileno(),))
                self.epoll.register(socket_to_activate.fileno(), RW)
            self.sockets_to_activate = []

        events = self.epoll.poll(timeout=timeout)

        self.do_timer_events()

        for fd, event in events:
            sock = self.fd_to_sock[fd]

            # Errors
            try:
                if event & (select.EPOLLERR | select.EPOLLHUP):
                    logger.debug('Socket %s has failed', fd)
                    raise SocketFailed()

                if event & select.EPOLLIN:
                    sock.on_read()

                if event & select.EPOLLOUT:
                    sock.on_write()
                    # I'm done with sending for now
                    if len(sock.data_to_send) == 0 and len(
                            sock.priority_queue) == 0:
                        self.epoll.modify(sock.fileno(), RO)

            except SocketFailed as e:
                logger.debug('Socket %s has raised %s', fd, e)
                self.close_socket(sock)

        # Do any of the sockets want to send data Re-register them
        for sock in six.itervalues(self.fd_to_sock):
            if sock.wants_to_send_data():
                self.epoll.modify(sock.fileno(), RW)

    def close_socket(self, sock):  # type: (BaseSocket) -> None
        self.epoll.unregister(sock.fileno())
        super(EpollListener, self).close_socket(sock)

    def shutdown(self):
        """
        Forcibly close all sockets that this manages (calling their on_fail's),
        and close the object.

        This object is unusable after this call.
        """
        super(EpollListener, self).shutdown()
        self.epoll.close()

    def activate(self, sock):  # type: (BaseSocket) -> None
        super(EpollListener, self).activate(sock)
        with self.socket_activation_lock:
            self.sockets_to_activate.append(sock)

    def register(self, sock, on_read=lambda data: None,
                 on_fail=lambda: None):
        """
        Add a socket to be listened for by the loop.

        Please note that .activate() will be later called on this socket.

        :param sock: a socket instance (as returned by socket module)
        :param on_read: callable(data) to be called with received data
        :param on_fail: callable() to be called when socket fails

        :return: a BaseSocket instance to use instead of this socket
        """
        return EpollSocket(sock, on_read, on_fail=on_fail, listener=self)
