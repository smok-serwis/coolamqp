# coding=UTF-8
from __future__ import print_function, division, absolute_import

"""
That funny type, field-table...

A field-value is of form (value::any, type::unicode)

An array is of form [field-value1, field-value2, ...]

A table is of form ( (name1::bytes, fv1), (name2::bytes, fv2), ...)


NOTE: it's not buffers, it's memoryview all along
"""

import struct
import io
import six


def _tobuf(buf, pattern, *vals):  # type: (io.BytesIO, str, *tp.Any) -> int
    return buf.write(struct.pack(pattern, *vals))


def _tobufv(buf, value, pattern, *vals):  # type: (io.BytesIO, bytes, str, *tp.Any) -> None
    _tobuf(buf, pattern, *vals)
    buf.write(value)


def _frombuf(pattern, buf, offset):
    return struct.unpack_from(pattern, buf, offset)


def enframe_decimal(buf, v):  # convert decimal to bytes
    dps = 0
    for k in six.moves.xrange(20):
        k = v * (10 ** dps)
        if abs(k - int(k)) < 0.00001:  # epsilon
            return _tobuf(buf, '!BI', dps, k)

    raise ValueError('Could not convert %s to decimal', v)


def deframe_decimal(buf, offset):
    scale, val = _frombuf('!BI', buf, offset)
    return val / (10 ** scale), 5


def deframe_shortstr(buf, offset):  # -> value, bytes_eaten
    ln, = _frombuf('!B', buf, offset)
    return buf[offset + 1:offset + 1 + ln], 1 + ln


def enframe_shortstr(buf, value):
    _tobufv(buf, value, '!B', len(value))


def deframe_longstr(buf, offset):  # -> value, bytes_eaten
    ln, = _frombuf('!I', buf, offset)
    return buf[offset + 4:offset + 4 + ln], 4 + ln


def enframe_longstr(buf, value):
    _tobufv(buf, value, '!I', len(value))


def _c2none(buf, v):
    return None


FIELD_TYPES = {
    # length, struct, (option)to_bytes (callable(buffer, value)),
    #                 (option)from_bytes (callable(buffer, offset) ->
    #                                           value, bytes_consumed),
    #                 (option)get_len (callable(value) -> length in bytes)
    't': (1, '!?'),  # boolean
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
    'D': (5, None, enframe_decimal, deframe_decimal),  # decimal-value
    's': (
        None, None, enframe_shortstr, deframe_shortstr,
        lambda val: len(val) + 1),
    # shortstr
    'S': (
        None, None, enframe_longstr, deframe_longstr,
        lambda val: len(val) + 4),
    # longstr
    'T': (8, '!Q'),
    'V': (0, None, _c2none, _c2none, 0),
    # rendered as None
}

if six.PY3:
    chrpy3 = chr
else:
    chrpy3 = lambda x: x


def enframe_field_value(buf, fv):
    value, type = fv
    buf.write(type.encode('utf8'))

    opt = FIELD_TYPES[type]

    if opt[1] is not None:
        _tobuf(buf, opt[1], value)
    else:
        opt[2](buf, value)


def deframe_field_value(buf, offset):  # -> (value, type), bytes_consumed
    start_offset = offset
    field_type = chrpy3(buf[offset])
    offset += 1

    if field_type not in FIELD_TYPES.keys():
        raise ValueError('Unknown field type %s!', (repr(field_type),))

    opt = FIELD_TYPES[field_type]

    if opt[1] is not None:
        field_val, = struct.unpack_from(FIELD_TYPES[field_type][1], buf,
                                        offset)
        offset += opt[0]
    else:
        field_val, delta = opt[3](buf, offset)
        offset += delta

    return (field_val, field_type), offset - start_offset


def deframe_array(buf, offset):
    start_offset = offset
    ln, = _frombuf('!I', buf, offset)
    offset += 4

    values = []
    while offset < (start_offset + 1 + ln):
        v, t, delta = deframe_field_value(buf, offset)
        offset += delta
        values.append((v, t))

    if offset != start_offset + 4 + ln:
        raise ValueError(
            'Array longer than expected, took %s, expected %s bytes',
            (offset - (start_offset + ln + 4), ln + 4))

    return values, ln + 4


def enframe_array(buf, array):
    _tobuf(buf, '!I', frame_array_size(array) - 4)
    for fv in array:
        enframe_field_value(buf, fv)


def enframe_table(buf, table):  # type (tp.BinaryIO, table) -> None
    """
    Write AMQP table to buffer

    :param buf: target buffer to write to
    :param table: table to write
    """
    _tobuf(buf, '!I', frame_table_size(table) - 4)

    for name, fv in table:
        _tobufv(buf, name, '!B', len(name))
        enframe_field_value(buf, fv)


def deframe_table(buf, start_offset):  # -> (table, bytes_consumed)
    """:return: tuple (table, bytes consumed)"""
    offset = start_offset
    table_length, = struct.unpack_from('!L', buf, start_offset)
    offset += 4

    # we will check if it's really so.
    fields = []

    while offset < (start_offset + table_length + 4):
        field_name, ln = deframe_shortstr(buf, offset)
        offset += ln
        fv, delta = deframe_field_value(buf, offset)
        offset += delta
        fields.append((field_name.tobytes(), fv))

    if offset > (start_offset + table_length + 4):
        raise ValueError(
            'Table turned out longer than expected! Found %s bytes expected %s',
            (offset - start_offset, table_length))

    return fields, table_length + 4


def frame_field_value_size(fv):
    v, t = fv
    if FIELD_TYPES[t][0] is None:
        return FIELD_TYPES[t][4](v) + 1
    else:
        return FIELD_TYPES[t][0] + 1


def frame_array_size(array):
    return 4 + sum(frame_field_value_size(fv) for fv in array)


def frame_table_size(table):
    """
    :return: length of table representation, in bytes, INCLUDING length
     header"""
    return 4 + sum(1 + len(k) + frame_field_value_size(fv) for k, fv in table)


FIELD_TYPES['A'] = (None, None, enframe_array, deframe_array, frame_array_size)
FIELD_TYPES['F'] = (None, None, enframe_table, deframe_table, frame_table_size)
