# coding=UTF-8
from __future__ import absolute_import, division, print_function

import io


class SendingFramer(object):
    """
    Assembles AMQP framing from received data and orchestrates their upload via a socket.

    Just call with .put(data) and get framing by iterator .framing().

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

    def __init__(self, on_send=lambda data: None):
        """
        :param on_send: a callable(data, priority=False) that can be called with some data to send
            data will always be entire AMQP frames!
        """
        self.on_send = on_send

    def send(self, frames, priority=False):
        """
        Schedule to send some frames.
        :param frames: list of AMQPFrame instances
        :param priority: preempty existing frames
        """
        length = sum(frame.get_size() for frame in frames)
        buf = io.BytesIO(bytearray(length))

        for frame in frames:
            frame.write_to(buf)

        q = buf.getvalue()
        self.on_send(q, priority)
