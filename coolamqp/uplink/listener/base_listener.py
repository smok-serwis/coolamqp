from abc import ABCMeta, abstractmethod
import heapq
import typing as tp
import six
from coolamqp.utils import monotonic


class BaseListener(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.fd_to_sock = {}    # type: tp.Dict[int, BaseSocket]
        self.time_events = []  # type: tp.List[tp.Tuple[float, int, tp.Callable[[], None]]]

    def do_timer_events(self):
        # Timer events
        mono = monotonic()
        while len(self.time_events) > 0 and (self.time_events[0][0] < mono):
            ts, fd, callback = heapq.heappop(self.time_events)
            callback()

    def oneshot(self, sock, delta, callback):
        """
        A socket registers a time callback
        :param sock: BaseSocket instance
        :param delta: "this seconds after now"
        :param callback: callable/0
        """
        if sock.fileno() in self.fd_to_sock:
            heapq.heappush(self.time_events, (monotonic() + delta,
                                              sock.fileno(),
                                              callback
                                              ))

    def noshot(self, sock):     # type: (BaseSocket) -> None
        """
        Clear all one-shots for a socket
        :param sock: BaseSocket instance
        """
        fd = sock.fileno()
        self.time_events = [q for q in self.time_events if q[1] != fd]

    @abstractmethod
    def wait(self, timeout=1):
        """
        This will be executed in a loop.

        This must call .do_timer_events()
        """

    def close_socket(self, sock):   # type: (BaseSocket) -> None
        del self.fd_to_sock[sock.fileno()]
        sock.on_fail()
        self.noshot(sock)
        sock.close()

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
            heapq.heappush(self.time_events, (monotonic() + delta,
                                              sock.fileno(),
                                              callback
                                              ))

    def activate(self, sock):  # type: (BaseSocket) -> None
        self.fd_to_sock[sock.fileno()] = sock

    @abstractmethod
    def register(self, sock,                    # type: socket.socket
                 on_read=lambda data: None,     # type: tp.Callable[[bytearray], None]
                 on_fail=lambda: None         # type: tp.Callable[[], None]
                 ):                     # type: () -> BaseSocket
        """
        This has to return a particular Socket instance, adapted to the needs of the listener.

        :param sock: a socket instance (as returned by socket module)
        :param on_read: callable(data) to be called with received data
        :param on_fail: callable() to be called when socket fails

        :return: a BaseSocket's subclass instance to use instead of this socket
        """
