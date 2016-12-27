# coding=UTF-8
from __future__ import absolute_import, division, print_function
import struct
import io
import six
import collections
import socket


from coolamqp.framing.streams.exceptions import InvalidDataError


class ReceivingFormatter(object):
    """
    Assembles AMQP frames from received data.

    Just call with .put(data) and get frames by
    iterator .frames().

    Not thread safe.
    """
    def __init__(self, sock):
        self.chunks = collections.deque()   # all received data
        self.total_data_len = 0
        self.header = None  # or type, channel, size
        self.frames = collections.deque()   # for

    def receive_from_socket(self, data):
        self.total_data_len += len(data)
        self.chunks.append(buffer(data))

    def get_frames(self):
        """
        An iterator to return frames pending for read.

        :raises ValueError:
        :return:
        """

    def __got_frame(self, type_, channel, payload, frame_end):
        """
        New frame!

        Try decoding
        """


    def __statemachine(self):
        if self.header is None and self.total_data_len > 7:
            a = bytearray()
            while len(a) < 7:
                if len(self.chunks[0]) <= (len(a) - 7):  # we will need a next one
                    a.extend(self.chunks.popleft())
                else:
                    a.extend(self.chunks[0:len(a-7)])
                    self.chunks[0] = buffer(self.chunks[0], len(a)-7)
            self.header = struct.unpack('!BHI', a)

        if (self.header is not None) and self.total_data_len >= (self.header[2]+1):
            if len(self.chunks[0]) > self.header[2]+1:
                # We can subslice it - it's very fast
                payload = buffer(self.chunks[0], self.header[2])
                frame_end = self.chunks[self.header[2]]
                self.chunks[0] = buffer(self.chunks[0], self.header[2]+1)

            else:
                # Construct a separate buffer :(
                payload = io.BytesIO()
                while payload.tell() < self.header[2]:
                    remaining = self.header[2] - payload.tell()

                    if remaining >= self.chunks[0]:
                        chunk = self.chunks.popleft()
                        payload.write(self.chunks.popleft())
                        self.total_data_len -= len(chunk)
                    else:
                        self.total_data_len -= remaining
                        payload.write(buffer(self.chunks[0], 0, remaining))
                        self.chunks[0] = buffer(self.chunks[0], remaining)

                # Get last byte
                if len(self.chunks[0]) == 1:
                    frame_end = self.chunks.pop()[0]
                else:
                    frame_end = self.chunks[0][0]
                    self.chunks[0] = buffer(self.chunks[0], 1)

                self.__got_frame(self.header[0], self.header[1], payload.getvalue(), frame_end)
                self.header = None


