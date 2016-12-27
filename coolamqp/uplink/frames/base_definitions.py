# coding=UTF-8
"""
Used for definitions
"""
from __future__ import absolute_import, division, print_function

import struct

from coolamqp.uplink.frames.base import AMQPPayload



class AMQPClass(object):
    """An AMQP class"""


class AMQPContentPropertyList(object):
    """
    A class is intmately bound with content and content properties
    """
    PROPERTIES = []


class AMQPMethodPayload(AMQPPayload):
    RESPONSE_TO = None
    REPLY_WITH = []
    FIELDS = []

    def write_to(self, buf):
        """
        Write own content to target buffer - starting from LENGTH, ending on FRAME_END
        :param buf: target buffer
        """
        from coolamqp.uplink.frames.definitions import FRAME_END

        if self.IS_CONTENT_STATIC:
            buf.write(self.STATIC_CONTENT)
        else:
            buf.write(struct.pack('!I', self.get_size()+2))
            buf.write(self.BINARY_HEADER)
            self.write_arguments(buf)
            buf.write(chr(FRAME_END))

    def get_size(self):
        """
        Calculate the size of this frame.

        :return: int, size of argument section
        """
        raise NotImplementedError()

    def write_arguments(self, buf):
        """
        Write the argument portion of this frame into buffer.

        :param buf: buffer to write to
        :return: how many bytes written
        :raise ValueError: some field here is invalid!
        """
        raise NotImplementedError()

    @staticmethod
    def from_buffer(buf, offset):
        """
        Construct this frame from a buffer

        :param buf: a buffer to construct the frame from
        :type buf: buffer or memoryview
        :param offset: offset the argument portion begins at
        :type offset: int
        :return: tuple of (an instance of %s, amount of bytes consumed as int)
        :raise ValueError: invalid data
        """
        raise NotImplementedError('')

