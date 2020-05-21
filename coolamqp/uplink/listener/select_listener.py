# coding=UTF-8
from __future__ import absolute_import, division, print_function

import logging
import select
import socket

import six

from coolamqp.uplink.listener.socket import SocketFailed, BaseSocket
from coolamqp.uplink.listener.base_listener import BaseListener

logger = logging.getLogger(__name__)

RO = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
RW = RO | select.EPOLLOUT


class SelectListener(BaseListener):
    """
    A listener using select
    """

    def wait(self, timeout=0.5):
        rds_and_exs = []        # waiting both for read and for exception
        wrs = []                # waiting for write
        for sock in six.itervalues(self.fd_to_sock):
            rds_and_exs.append(sock)
            if sock.wants_to_send_data():
                wrs.append(sock)

        self.do_timer_events()

        try:
            rds, wrs, exs = select.select(rds_and_exs, wrs, rds_and_exs, timeout)
        except (select.error, socket.error, IOError):
            for sock in rds_and_exs:
                try:
                    select.select([sock], [], [], timeout=0)
                except (select.error, socket.error, IOError):
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

    def register(self, sock, on_read=lambda data: None,
                 on_fail=lambda: None):
        """
        Add a socket to be listened for by the loop.

        :param sock: a socket instance (as returned by socket module)
        :param on_read: callable(data) to be called with received data
        :param on_fail: callable() to be called when socket fails

        :return: a BaseSocket instance to use instead of this socket
        """
        return BaseSocket(sock, on_read, on_fail=on_fail, listener=self)
