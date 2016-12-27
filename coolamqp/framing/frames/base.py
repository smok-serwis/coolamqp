# coding=UTF-8
from __future__ import absolute_import, division, print_function
import struct
import logging
import six

logger = logging.getLogger(__name__)


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


def dec_to_bytes(buf, v):
    dps = 0
    for k in six.moves.xrange(20):
        k = v * (10 ** dps)
        if abs(k-int(k)) < 0.00001: # epsilon
            return buf.write(struct.pack('!BI', dps, k))

    logger.critical('Cannot convert %s to decimal, substituting with 0', repr(v))
    buf.write(b'\x00\x00\x00\x00')


FIELD_TYPES = {
        # length, struct, (option)formatter_to_bytes
    't': (1, '!?'),      # boolean
    'b': (1, '!b'),
    'B': (1, '!B'),
    'U': (2, '!H'),
    'u': (2, '!h'),
    'I': (4, '!I'),
    'i': (4, '!i'),
    'L': (8, '!Q'),
    'l': (8, '!q'),
    'f': (4, '!f'),
    'd': (8, '!d'),
    'D': (5, None, dec_to_bytes), # decimal-value
    's': (None, None, lambda buf, v: buf.write(struct.pack('B', len(v)) + v)),       # short-string
    'S': (None, None, lambda buf, v: buf.write(struct.pack('!I', len(v)) + v)),  # long-string
    'A': (None, None),  # field-array
    'T': (8, '!Q'),
    'V': (0, ''),
}




"""
A table is of form:
[
    (name::bytes, value::any, type::bytes(len=1)),
    ...

]
"""


def _enframe_table(buf, table):
    """
    Write AMQP table to buffer
    :param buf:
    :param table:
    :return:
    """
    buf.write(struct.pack('!L', _frame_table_size(table)))

    for name, value, type in table:
        buf.write(struct.pack('!B', len(name)))
        buf.write(name)
        buf.write(type)

        opt = FIELD_TYPES[opt]

        if type == 'F': # nice one
            _enframe_table(buf, value)
        elif type == 'V':
            continue
        elif len(opt) == 2: # can autoframe
            buf.write(struct.pack(opt[1], value))
        else:
            opt[2](buf, value)


def _deframe_table(buf, start_offset): # helper - convert bytes to table
    """:return: tuple (table, bytes consumed)"""


def _frame_table_size(table):
    """:return: length of table representation, in bytes, WITHOUT length header"""


class AMQPClass(object):
    pass


class AMQPPayload(object):
    """Payload is something that can write itself to bytes,
    or at least provide a buffer to do it."""

    def write_arguments(self, buf):
        """
        Emit itself into a buffer

        :param buf: buffer to write to (will be written using .write)
        """


class AMQPMethod(object):
    RESPONSE_TO = None
    REPLY_WITH = []
    FIELDS = []

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
        """
        raise NotImplementedError('')




class AMQPFrame(object):
    def __init__(self, channel, payload):
        self.channel = channel
        self.payload = payload