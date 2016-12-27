# coding=UTF-8
from __future__ import absolute_import, division, print_function
import struct
"""bytes <-> Frame's"""

from coolamqp.framing.frames import IDENT_TO_METHOD, FRAME_END, FRAME_METHOD

HDR = b'AMQP\x00\x00\x00\x01'


class AMQPFrame(object):
    def __init__(self, type_, channel, payload):



def serialize_method(channel, method):
    """Return an AMQP frame"""
    strs = []
    method.write(lambda s: strs.append(s))
    payload_len = sum(len(x) for x in strs)
    return b''.join([struct.pack('!BHI', FRAME_METHOD, channel, payload_len)] + strs + [chr(FRAME_END)])

def try_frame(buf, offset):
    """
    Try to make sense out of a buffer and decode a frame.
    :param buf:
    :param offset:
    :return:
    """


def to_packet(type_, channel, payload, size=None, frame_end=None):
    """
    :type payload: six.binary_type
    :type frame_end: six.binary_type
    """
    size = size or len(payload)
    frame_end = frame_end or FRAME_END
    return struct.pack('!BHI', type_, channel, size) + payload + FRAME_END
