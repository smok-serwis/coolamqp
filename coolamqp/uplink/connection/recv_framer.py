# coding=UTF-8
from __future__ import absolute_import, division, print_function

import collections
import io
import struct

import six

from coolamqp.framing.definitions import FRAME_HEADER, FRAME_HEARTBEAT, \
    FRAME_END, FRAME_METHOD, FRAME_BODY
from coolamqp.framing.frames import AMQPBodyFrame, AMQPHeaderFrame, \
    AMQPHeartbeatFrame, AMQPMethodFrame

FRAME_TYPES = {
    FRAME_HEADER: AMQPHeaderFrame,
    FRAME_BODY: AMQPBodyFrame,
    FRAME_METHOD: AMQPMethodFrame
}

ordpy2 = ord if six.PY2 else lambda x: x


class ReceivingFramer(object):
    """
    Assembles AMQP framing from received data.

    Just call with .put(data) upon receiving,
    and on_frame will be called with fresh frames.

    Not thread safe.

    State machine
        (frame_type is None)  and has_bytes(1)        ->
                (frame_type <- bytes(1))

        (frame_type is HEARTBEAT) and has_bytes(AMQPHeartbeatFrame.LENGTH-1)
                      ->          (output_frame, frame_type <- None)
        (frame_type is not HEARTBEAT and not None) and has_bytes(6)  ->
                                       (frame_channel <- bytes(2),
                                         frame_size <- bytes(4))

        (frame_size is not None) and has_bytes(frame_size+1)    ->
                    (output_frame,

                                    frame_type <- None
                                    frame_size < None)
    """

    def __init__(self, on_frame=lambda frame: None):
        self.chunks = collections.deque()  # all received data
        self.total_data_len = 0

        self.frame_type = None
        self.frame_channel = None
        self.frame_size = None

        self.bytes_needed = None  # bytes needed for a new frame
        self.on_frame = on_frame

    def put(self, data):
        """
        Called upon receiving data.

        May result in any number of .on_frame() calls
        :param data: received data
        """
        self.total_data_len += len(data)
        self.chunks.append(memoryview(data))

        while self._statemachine():
            pass

    def _extract_single_byte(self):
        return ordpy2(self._extract(1)[0])

    def _extract(self, up_to):
        """
        return up to up_to bytes from current chunk, switch if necessary
        """
        assert self.total_data_len >= up_to, \
            'Tried to extract %s but %s remaining' % (
                up_to, self.total_data_len)
        if up_to >= len(self.chunks[0]):
            q = self.chunks.popleft()
        else:
            q = self.chunks[0][:up_to]
            self.chunks[0] = self.chunks[0][up_to:]

        self.total_data_len -= len(q)
        assert len(q) <= up_to, 'extracted %s but %s was requested' % (
            len(q), up_to)
        return q

    def _statemachine(self):
        # state rule 1
        if self.frame_type is None and self.total_data_len > 0:
            self.frame_type = self._extract_single_byte()

            if self.frame_type not in (
                    FRAME_HEARTBEAT, FRAME_HEADER, FRAME_METHOD, FRAME_BODY):
                raise ValueError('Invalid frame')

            return True

        # state rule 2
        elif (self.frame_type == FRAME_HEARTBEAT) and (
                self.total_data_len >= AMQPHeartbeatFrame.LENGTH - 1):
            data = b''
            while len(data) < AMQPHeartbeatFrame.LENGTH - 1:
                data = data + self._extract(
                    AMQPHeartbeatFrame.LENGTH - 1 - len(data)).tobytes()

            if data != AMQPHeartbeatFrame.DATA[1:]:
                # Invalid heartbeat frame!
                raise ValueError('Invalid AMQP heartbeat')

            self.on_frame(AMQPHeartbeatFrame())
            self.frame_type = None

            return True

        # state rule 3
        elif (self.frame_type != FRAME_HEARTBEAT) and (
                self.frame_type is not None) and (
                self.frame_size is None) and (
                self.total_data_len > 6):
            hdr = b''
            while len(hdr) < 6:
                hdr = hdr + self._extract(6 - len(hdr)).tobytes()

            self.frame_channel, self.frame_size = struct.unpack('!HI', hdr)

            return True

        # state rule 4
        elif (self.frame_size is not None) and (
                self.total_data_len >= (self.frame_size + 1)):

            if len(self.chunks[0]) >= self.frame_size:
                # We can subslice it - it's very fast
                payload = self._extract(self.frame_size)
            else:
                # Construct a separate buffer :(
                payload = io.BytesIO()
                while payload.tell() < self.frame_size:
                    payload.write(
                        self._extract(self.frame_size - payload.tell()))

                assert payload.tell() <= self.frame_size

                payload = memoryview(payload.getvalue())

            if self._extract_single_byte() != FRAME_END:
                raise ValueError('Invalid frame end')

            try:
                frame = FRAME_TYPES[self.frame_type].unserialize(
                    self.frame_channel, payload)
            except ValueError:
                raise

            self.on_frame(frame)
            self.frame_type = None
            self.frame_size = None

            return True
        return False
