# coding=UTF-8
from __future__ import absolute_import, division, print_function

import collections
import threading
import io
import socket


class SendingOperator(object):
    """
    Assembles AMQP frames from received data and orchestrates their upload via a socket.

    Just call with .put(data) and get frames by iterator .frames().

    Not thread safe.

    State machine
        (frame_type is None)  and has_bytes(1)        ->          (frame_type <- bytes(1))

        (frame_type is HEARTBEAT) and has_bytes(3)  ->          (output_frame, frame_type <- None)
        (frame_type is not HEARTBEAT and not None) and has_bytes(6)  ->      (frame_channel <- bytes(2),
                                                                 frame_size <- bytes(4))

        (frame_size is not None) and has_bytes(frame_size+1)    ->  (output_frame,
                                                                            frame_type <- None
                                                                            frame_size < None)
    """
    def __init__(self, sock, on_fail=lambda e: None,
                             on_close=lambda: None):
        """
        :param sock: a non-timeouting socket
        :param on_fail: callable(exception) to call when socket fails
        :param on_close: callable(exception) to call when socket closes
        """
        self.sock = sock
        self.to_send = collections.deque()      # either bytes, bytearrays and buffers, or tuple of
                                                #    (callable/0, callable/1)

        self.on_fail = on_fail
        self.on_close = on_close

        self.failed = False

    def _failed(self, e):
        """Discard all to_send, run on_fail callables"""
        self.failed = True
        self.on_fail(e)

        for order in self.to_send:
            if isinstance(order, tuple) and len(order) == 2:
                on_done, on_fail = order
                if on_fail is not None:
                    on_fail(e)

        self.to_send = collections.deque()

    def run_sending_loop(self):
        while len(self.to_send) > 0:
            if isinstance(self.to_send[0], tuple) and len(self.to_send[0]) == 2:
                on_done, on_fail = self.to_send.popleft()
                if on_done is not None:
                    on_done()
            else:
                try:
                    sent_bytes = self.sock.send(self.to_send[0])
                except (IOError, socket.error) as e:
                    self._failed(e)
                    return

                if sent_bytes == len(self.to_send[0]):
                    # Fetch next fragment
                    self.to_send.popleft()
                else:
                    # slice current buffer
                    self.to_send[0] = buffer(self.to_send[0], sent_bytes)

    def send(self, frames, on_done=None, on_fail=None):
        """
        Schedule to send some frames.
        :param frames: list of AMQPFrame instances
        :param on_done: callable/0 to call when this is done (frame_end of last frame has just left this PC)
        :param on_fail: callable(Exception) to call when something broke before the data could be sent.
        """
        length = sum(frame.get_size() for frame in frames)
        buf = io.BytesIO(bytearray(length))

        for frame in frames:
            frame.write_to(buf)

        self.to_send.append(buf.getvalue())
        if (on_done is not None) or (on_fail is not None):
            self.to_send.append(on_done, on_fail)

        self.run_sending_loop()
