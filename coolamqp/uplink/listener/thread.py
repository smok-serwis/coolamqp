# coding=UTF-8
from __future__ import absolute_import, division, print_function

import threading
import typing as tp

from coolamqp.objects import Callable
from coolamqp.uplink.listener.epoll_listener import EpollListener


class ListenerThread(threading.Thread):
    """
    A thread that does the listening.

    It automatically picks the best listener for given platform.
    """

    def __init__(self, name=None):  # type: (tp.Optional[str]) -> None
        threading.Thread.__init__(self, name='coolamqp/ListenerThread')
        self.daemon = True
        self.name = name or 'CoolAMQP'
        self.terminating = False
        self._call_next_io_event = Callable(oneshots=True)

    def call_next_io_event(self, callable):
        """
        Call callable after current I/O event is fully processed

        sometimes many callables are called in response to single
        I/O (eg. teardown, startup). This guarantees a call after
        all these are done.
        :param callable: callable/0
        """
        self._call_next_io_event()

    def terminate(self):
        self.terminating = True

    def init(self):
        """Called before start. It is not safe to fork after this"""
        self.listener = EpollListener()

    def activate(self, sock):
        self.listener.activate(sock)

    def run(self):
        try:
            import prctl
        except ImportError:
            pass
        else:
            prctl.set_name(self.name+' - AMQP listener thread')

        while not self.terminating:
            self.listener.wait(timeout=1)

        self.listener.shutdown()

    def register(self, sock, on_read=lambda data: None, on_fail=lambda: None):
        """
        Add a socket to be listened for by the loop.

        :param sock: a socket instance (as returned by socket module)
        :param on_read: callable(data) to be called with received data
        :param on_fail: callable() to be called when socket fails

        :return: a BaseSocket instance to use instead of this socket
        """
        return self.listener.register(sock, on_read, on_fail)
