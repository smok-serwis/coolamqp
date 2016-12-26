# coding=UTF-8
from __future__ import absolute_import, division, print_function
import struct
"""bytes <-> Frame's"""

from coolamqp.framing.definitions import FRAME_END

HDR = b'AMQP\x01\x01\x00\x09'



def to_packet(type_, channel, payload, size=None, frame_end=None):
    """
    :type payload: six.binary_type
    :type frame_end: six.binary_type
    """
    size = size or len(payload)
    frame_end = frame_end or FRAME_END
    return struct.pack('!BHI', type_, channel, size) + payload + FRAME_END
