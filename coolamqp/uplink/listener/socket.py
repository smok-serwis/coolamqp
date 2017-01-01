# coding=UTF-8
from __future__ import absolute_import, division, print_function
import collections
import socket


class SocketFailed(IOError):
    """Failure during socket operation. It needs to be discarded."""


class BaseSocket(object):
    """
    Base class for sockets provided to listeners.

    This is based on a standard TCP socket.

    To be instantiated only by Listeners.
    """

    def __init__(self, sock, on_read=lambda data: None,
                             on_time=lambda: None,
                             on_fail=lambda: None):
        """

        :param sock: socketobject
        :param on_read: callable(data) to be called when data is read.
            Listener thread context
            Raises ValueError on socket should be closed
        :param on_time: callable() when time provided by socket expires
        :param on_fail: callable() when socket is dead and to be discarded.
            Listener thread context.
            Socket descriptor will be handled by listener.
            This should not
        """
        assert sock is not None
        self.sock = sock
        self.data_to_send = collections.deque()
        self.my_on_read = on_read
        self.on_fail = on_fail
        self.on_time = on_time

    def send(self, data):
        """
        Schedule to send some data

        :param data: data to send, or None to terminate this socket
        """
        raise Exception('Abstract; listener should override that')

    def oneshot(self, seconds_after, callable):
        """
        Set to fire a callable N seconds after
        :param seconds_after: seconds after this
        :param callable: callable/0
        """
        raise Exception('Abstract; listener should override that')

    def noshot(self):
        """
        Clear all time-delayed callables.

        This will make no time-delayed callables delivered if ran in listener thread
        """
        raise Exception('Abstract; listener should override that')

    def on_read(self):
        """Socket is readable, called by Listener"""
        try:
            data = self.sock.recv(2048)
        except (IOError, socket.error):
            raise SocketFailed()

        if len(data) == 0:
            raise SocketFailed()

        try:
            self.my_on_read(data)
        except ValueError:
            raise SocketFailed()

    def on_write(self):
        """
        Socket is writable, called by Listener
        :return: (bool) I finished sending all the data for now
        :raises SocketFailed: on socket error
        """
        if len(self.data_to_send) == 0:
            return True # No data to send

        while len(self.data_to_send) > 0:

            if self.data_to_send[0] is None:
                raise SocketFailed() # We should terminate the connection!

            try:
                sent = self.sock.send(self.data_to_send[0])
            except (IOError, socket.error):
                raise SocketFailed()

            if sent < len(self.data_to_send[0]):
                # Not everything could be sent
                self.data_to_send[0] = buffer(self.data_to_send[0], sent)
                return False    # I want to send more
            else:
                self.data_to_send.popleft()     # Sent all!

        return True # all for now

    def fileno(self):
        """Return descriptor number"""
        return self.sock.fileno()

    def close(self):
        """Close this socket"""
        self.sock.close()