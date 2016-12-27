# coding=UTF-8
from __future__ import absolute_import, division, print_function
import struct
import logging
import six

logger = logging.getLogger(__name__)


AMQP_HELLO_HEADER = b'AMQP\x00\x00\x09\x01'


# name => (length|None, struct ID|None, reserved-field-value : for struct if structable, bytes else, length of default)
BASIC_TYPES = {'bit': (None, None, "0", None),          # special case
               'octet': (1, 'B', "b'\\x00'", 1),
               'short': (2, 'H', "b'\\x00\\x00'", 2),
               'long': (4, 'I', "b'\\x00\\x00\\x00\\x00'", 4),
               'longlong': (8, 'Q', "b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'", 8),
               'timestamp': (8, 'L', "b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'", 8),
               'table': (None, None, "b'\\x00\\x00\\x00\\x00'", 4),          # special case
               'longstr': (None, None, "b'\\x00\\x00\\x00\\x00'", 4),        # special case
               'shortstr': (None, None, "b'\\x00'", 1),                        # special case
               }

DYNAMIC_BASIC_TYPES = ('table', 'longstr', 'shortstr')



class AMQPFrame(object):        # base class for frames
    FRAME_TYPE = None   # override me!

    def __init__(self, channel):
        self.channel = channel

    def write_to(self, buf):
        """
        Write a complete frame to buffer

        This writes type and channel ID.
        """
        buf.write(struct.pack('!BH', self.FRAME_TYPE, self.channel))

    @staticmethod
    def unserialize(channel, payload_as_buffer):
        """
        Unserialize from a buffer.
        Buffer starts at frame's own payload - type, channel and size was already obtained.
        Payload does not contain FRAME_EMD.
        AMQPHeartbeatFrame does not have to implement this.
        """
        raise NotImplementedError('Override me')

    def get_size(self):
        """
        Return size of this frame, in bytes, from frame type to frame_end
        :return: int
        """
        raise NotImplementedError()


class AMQPPayload(object):
    """Payload is something that can write itself to bytes,
    or at least provide a buffer to do it."""

    def write_to(self, buf):
        """
        Emit itself into a buffer, from length to FRAME_END

        :param buf: buffer to write to (will be written using .write)
        """

    def get_size(self):
        """
        Return size of this payload
        :return: int
        """
        raise NotImplementedError()
