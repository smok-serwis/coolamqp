# coding=UTF-8
from __future__ import absolute_import, division, print_function

import logging

logger = logging.getLogger(__name__)

AMQP_HELLO_HEADER = b'AMQP\x00\x00\x09\x01'

# name => (length|None, struct ID|None, reserved-field-value : for struct if structable, bytes else, length of default)
BASIC_TYPES = {u'bit': (None, None, "0", None),  # special case
               u'octet': (1, 'B', "b'\\x00'", 1),
               u'short': (2, 'H', "b'\\x00\\x00'", 2),
               u'long': (4, 'I', "b'\\x00\\x00\\x00\\x00'", 4),
               u'longlong': (
                   8, 'Q', "b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'", 8),
               u'timestamp': (
                   8, 'Q', "b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'", 8),
               u'table': (None, None, "b'\\x00\\x00\\x00\\x00'", 4),
               # special case
               u'longstr': (None, None, "b'\\x00\\x00\\x00\\x00'", 4),
               # special case
               u'shortstr': (None, None, "b'\\x00'", 1),  # special case
               }

DYNAMIC_BASIC_TYPES = (u'table', u'longstr', u'shortstr')


class AMQPFrame(object):  # base class for framing
    FRAME_TYPE = None  # override me!

    def __init__(self, channel):
        self.channel = channel

    def write_to(self, buf):
        """
        Write a complete frame to buffer

        This writes type and channel ID.
        """
        # DO NOT UNCOMMENT buf.write(struct.pack('!BH', self.FRAME_TYPE, self.channel))
        raise NotImplementedError(
            'Please write the frame type and channel in child classes, its faster that way ')

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
        raise NotImplementedError('Override me')


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


class AMQPClass(object):
    """An AMQP class"""


class AMQPContentPropertyList(object):
    """
    A class is intmately bound with content and content properties.

    WARNING: BE PREPARED that if you receive a content from the network,
    string values will be memoryviews. Use .tobytes() to correct that.
    If YOU create a property list, they will be bytes all right.
    """
    PROPERTIES = []

    # todo they are immutable, so they could just serialize themselves...

    def __str__(self):
        return '<AMQPContentPropertyList>'

    def get(self, property_name, default=None):
        """
        Return a particular property, or default if not defined
        :param property_name: property name, unicode
        :param default: default value
        :return: memoryview or bytes
        """
        return getattr(self, property_name, default)

    @staticmethod
    def zero_property_flags(property_flags):
        """
        Given a binary property_flags, set all bit properties to 0.

        This leaves us with a canonical representation, that can be used
        in obtaining a particular property list
        :param property_flags: binary
        :return: binary
        """
        # this is a default implementation.
        # compiler should emit it's own when the content property list has a
        # possible bit field
        return property_flags

    def write_to(self, buf):
        """Serialize itself (flags + values) to a buffer"""
        raise Exception(u'This is an abstract method')

    @staticmethod
    def from_buffer(self, buf, start_offset):
        """
        Return an instance of self, loaded from a buffer.

        This does not have to return length, because it is always passed exactly enough of a buffer.

        Buffer HAS TO start at property_flags
        """
        raise Exception(u'This is an abstract method')

    def get_size(self):
        """
        How long is property_flags + property_values
        :return: int
        """
        raise Exception(u'This is an abstract method')


class AMQPMethodPayload(AMQPPayload):
    RESPONSE_TO = None
    REPLY_WITH = []
    FIELDS = []

    def get_size(self):
        """
        Calculate the size of this frame.

        :return: int, size of argument section
        """
        if self.IS_CONTENT_STATIC:
            return len(
                self.STATIC_CONTENT) - 4 - 4 - 1  # minus length, class, method, frame_end

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
