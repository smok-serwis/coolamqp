# coding=UTF-8
from __future__ import absolute_import, division, print_function
import struct
import io
import six
import collections
import socket

from coolamqp.framing.frames.definitions import FRAME_HEADER, FRAME_HEARTBEAT, FRAME_END, FRAME_METHOD, FRAME_BODY
from coolamqp.framing.frames.frames import AMQPBodyFrame, AMQPHeaderFrame, AMQPHeartbeatFrame, AMQPMethodFrame
from coolamqp.framing.streams.exceptions import InvalidDataError


FRAME_TYPES = {
    FRAME_HEADER: AMQPHeaderFrame,
    FRAME_BODY: AMQPBodyFrame,
    FRAME_METHOD: AMQPMethodFrame
}


class ReceivingFormatter(object):
    """
    Assembles AMQP frames from received data.

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
    def __init__(self, sock):
        self.chunks = collections.deque()   # all received data
        self.total_data_len = 0

        self.frame_type = None
        self.frame_channel = None
        self.frame_size = None

        self.bytes_needed = None    # bytes needed for a new frame
        self.frames = collections.deque()   # for

    def put(self, data):
        self.total_data_len += len(data)
        self.chunks.append(buffer(data))

    def get_frames(self):   # -> iterator of AMQPFrame, raises ValueError
        """
        An iterator to return frames pending for read.

        :raises ValueError: invalid frame readed, kill the connection.
        :return: iterator with frames
        """
        while self._statemachine():
            pass

        while len(self.frames) > 0:
            yield self.frames.popleft()

    def _extract(self, up_to): # return up to up_to bytes from current chunk, switch if necessary
        if up_to >= len(self.chunks[0]):
            q =  self.chunks.popleft()
        else:
            q = buffer(self.chunks[0], 0, up_to)
            self.chunks[0] = buffer(self.chunks, up_to)
        self.total_data_len -= len(q)
        return q

    def _statemachine(self):   # -> bool, was any action taken?
        # state rule 1
        if self.frame_type is None and self.total_data_len > 0:
            self.frame_type = ord(self._extract(1))

            if self.frame_type not in (FRAME_HEARTBEAT, FRAME_HEADER, FRAME_METHOD, FRAME_BODY):
                raise ValueError('Invalid frame')

            return True

        # state rule 2
        if (self.frame_type == FRAME_HEARTBEAT) and (self.total_data_len > 3):
            data = b''
            while len(data) < 3:
                data = data + self._extract(3 - len(data))

            if data != AMQPHeartbeatFrame.DATA:
                # Invalid heartbeat frame!
                raise ValueError('Invalid AMQP heartbeat')

            self.frames.append(AMQPHeartbeatFrame())
            self.frame_type = None

            return True

        # state rule 3
        if (self.frame_type != FRAME_HEARTBEAT) and (self.frame_type is not None) and (self.total_data_len > 6):
            hdr = b''
            while len(hdr) < 6:
                hdr = hdr + self._extract(6 - len(hdr))

            self.frame_channel, self.frame_size = struct.unpack('!BI', hdr)

            return True

        # state rule 4
        if self.total_data_len >= (self.frame_size+1):

            if len(self.chunks[0]) >= self.total_data_len:
                # We can subslice it - it's very fast
                payload = self._extract(self.total_data_len)
            else:
                # Construct a separate buffer :(
                payload = io.BytesIO()
                while payload.tell() < self.total_data_len:
                    payload.write(self._extract(self.total_data_len - payload.tell()))

                payload = buffer(payload.getvalue())

            if ord(self._extract(1)) != FRAME_END:
                raise ValueError('Invalid frame end')

            try:
                frame = FRAME_TYPES[self.frame_type].unserialize(self.frame_channel, payload)
            except ValueError:
                raise

            self.frames.append(frame)
            self.frame_type = None
            self.frame_size = None

            return True
        return False