# coding=UTF-8
from __future__ import absolute_import, division, print_function

import threading
import logging
import typing as tp
import os
from coolamqp.objects import Callable
from coolamqp.uplink.listener.epoll_listener import EpollListener
from coolamqp.uplink.listener.select_listener import SelectListener
from coolamqp.uplink.listener.base_listener import BaseListener
from coolamqp.utils import prctl_set_name

logger = logging.getLogger(__name__)


def get_listener_class():   # type: () -> tp.Type[BaseListener]

    if 'COOLAMQP_FORCE_SELECT_LISTENER' in os.environ:
        return SelectListener

    try:
        import select
        select.epoll
    except AttributeError:
        return SelectListener   # we're running on a platform that doesn't support epoll

    try:
        import gevent.socket
    except ImportError:
        return EpollListener
    import socket

    if socket.socket is gevent.socket.socket:
        return SelectListener     # gevent is active

    return EpollListener


class ListenerThread(threading.Thread):
    """
    A thread that does the listening.

    It automatically picks the best listener for given platform.
    """

    def __init__(self, name=None):  # type: (tp.Optional[str])
        super(ListenerThread, self).__init__(name=name or 'coolamqp/ListenerThread')
        self.daemon = True
        self.name = name or 'CoolAMQP'
        self.terminating = False
        self._call_next_io_event = Callable(oneshots=True)
        self.listener = None        # type: BaseListener

    def call_next_io_event(self, callable):
        """
        Call callable after current I/O event is fully processed

        sometimes many callables are called in response to single
        I/O (eg. teardown, startup). This guarantees a call after
        all these are done.
        :param callable: callable/0
        """
        pass
#        self._call_next_io_event.add(callable) - dummy that out, causes AssertionError to appear

    def terminate(self):
        self.terminating = True

    def init(self):
        """Called before start. It is not safe to fork after this"""
        listener_class = get_listener_class()
        logger.info('Using %s as a listener' % (listener_class, ))
        self.listener = listener_class()

    def activate(self, sock):
        self.listener.activate(sock)

    def run(self):
        prctl_set_name(self.name + '- listener thread')

        while not self.terminating:
            self.listener.wait()
            self._call_next_io_event()

        self.listener.shutdown()

    def register(self, sock,  # type: socket.socket
                 on_read=lambda data: None,  # type: tp.Callable[[bytes], None]
                 on_fail=lambda: None      # type: tp.Callable[[], None]
                 ):
        """
        Add a socket to be listened for by the loop.

        :param sock: a socket instance (as returned by socket module)
        :param on_read: callable(data) to be called with received data
        :param on_fail: callable() to be called when socket fails

        :return: a BaseSocket instance to use instead of this socket
        """
        return self.listener.register(sock, on_read, on_fail)
