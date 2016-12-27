# coding=UTF-8
"""
Concrete frame definitions
"""
from __future__ import absolute_import, division, print_function

import struct

from coolamqp.uplink.frames.base import AMQPFrame
from coolamqp.uplink.frames.definitions import FRAME_METHOD, FRAME_HEARTBEAT, FRAME_BODY, FRAME_HEADER, FRAME_END, \
    IDENT_TO_METHOD


class AMQPMethodFrame(AMQPFrame):
    FRAME_TYPE = FRAME_METHOD

    def __init__(self, channel, payload):
        """
        :param channel: channel ID
        :param payload: AMQPMethodPayload instance
        """
        AMQPFrame.__init__(self, channel)
        self.payload = payload

    def write_to(self, buf):
        AMQPFrame.write_to(self, buf)
        self.payload.write_to(buf)


    @staticmethod
    def unserialize(channel, payload_as_buffer):
        clsmet = struct.unpack_from('!BB', payload_as_buffer, 0)

        try:
            method_payload_class = IDENT_TO_METHOD[clsmet]
            payload = method_payload_class.from_buffer(payload_as_buffer, 2)
        except KeyError:
            raise ValueError('Invalid class %s method %s' % clsmet)

        return AMQPMethodFrame(channel, payload)

    def get_size(self):
        return 10 + self.payload.get_size()


class AMQPHeaderFrame(AMQPFrame):
    FRAME_TYPE = FRAME_HEADER

    def __init__(self, channel, class_id, weight, body_size, property_flags, property_list):
        """
        :param channel:
        :param class_id:
        :param weight:
        :param body_size:
        :param property_flags:
        :param property_list:
        """
        AMQPFrame.__init__(self, channel)
        self.class_id = class_id
        self.weight = weight
        self.body_size = body_size
        self.property_flags = property_flags
        self.property_list = property_list

    def write_to(self, buf):
        AMQPFrame.write_to(self, buf)
        buf.write(struct.pack('!HHQH'))

    @staticmethod
    def unserialize(channel, payload_as_buffer):
        pass

    def get_size(self):
        raise NotImplementedError


class AMQPBodyFrame(AMQPFrame):
    FRAME_TYPE = FRAME_BODY

    def __init__(self, channel, data):
        AMQPFrame.__init__(self, channel)
        self.data = data

    def write_to(self, buf):
        AMQPFrame.write_to(self, buf)
        buf.write(buf)
        buf.write(chr(FRAME_END))

    @staticmethod
    def unserialize(channel, payload_as_buffer):
        return AMQPBodyFrame(channel, payload_as_buffer)

    def get_size(self):
        return 8 + len(self.data)


class AMQPHeartbeatFrame(AMQPFrame):
    FRAME_TYPE = FRAME_HEARTBEAT
    LENGTH = 4
    DATA = '\x00\x00\xCE'

    def __init__(self):
        AMQPFrame.__init__(self, 0)

    def write_to(self, buf):
        AMQPFrame.write_to(self, buf)
        buf.write(chr(FRAME_END))

    def get_size(self):
        return AMQPHeartbeatFrame.LENGTH
