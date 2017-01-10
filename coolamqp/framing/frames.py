# coding=UTF-8
"""
Concrete frame definitions
"""
from __future__ import absolute_import, division, print_function

import struct
import six

from coolamqp.framing.base import AMQPFrame
from coolamqp.framing.definitions import FRAME_METHOD, FRAME_HEARTBEAT, FRAME_BODY, FRAME_HEADER, FRAME_END, \
    IDENT_TO_METHOD, CLASS_ID_TO_CONTENT_PROPERTY_LIST


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
        if self.payload.IS_CONTENT_STATIC:
            buf.write(struct.pack('!BH', FRAME_METHOD, self.channel))
            buf.write(self.payload.STATIC_CONTENT)
        else:
            buf.write(struct.pack('!BHL', FRAME_METHOD, self.channel,
                                  4 + self.payload.get_size()))
            buf.write(self.payload.BINARY_HEADER)
            self.payload.write_arguments(buf)
            buf.write(chr(FRAME_END))

    @staticmethod
    def unserialize(channel, payload_as_buffer):
        clsmet = struct.unpack_from('!HH', payload_as_buffer, 0)

        try:
            method_payload_class = IDENT_TO_METHOD[clsmet]
            payload = method_payload_class.from_buffer(payload_as_buffer, 4)
        except KeyError:
            raise ValueError('Invalid class %s method %s' % clsmet)
        else:
            return AMQPMethodFrame(channel, payload)

    def get_size(self):
        # frame_header = (method(1) + channel(2) + length(4) + class(2) + method(2) + payload(N) + frame_end(1))
        return 12 + self.payload.get_size()


class AMQPHeaderFrame(AMQPFrame):
    FRAME_TYPE = FRAME_HEADER

    def __init__(self, channel, class_id, weight, body_size, properties):
        """
        :param channel: channel ID
        :param class_id: class ID
        :param weight: weight (lol wut?)
        :param body_size: size of the body to follow
        :param properties: a suitable AMQPContentPropertyList instance
        """
        AMQPFrame.__init__(self, channel)
        self.class_id = class_id
        self.weight = weight
        self.body_size = body_size
        self.properties = properties

    def write_to(self, buf):
        buf.write(struct.pack('!BHLHHQ', FRAME_HEADER, self.channel,
                              12+self.properties.get_size(), self.class_id, 0, self.body_size))
        self.properties.write_to(buf)
        buf.write(chr(FRAME_END))

    @staticmethod
    def unserialize(channel, payload_as_buffer):
        # payload starts with class ID
        class_id, weight, body_size = struct.unpack_from('!HHQ', payload_as_buffer, 0)
        properties = CLASS_ID_TO_CONTENT_PROPERTY_LIST[class_id].from_buffer(payload_as_buffer, 12)
        return AMQPHeaderFrame(channel, class_id, weight, body_size, properties)

    def get_size(self):
        # frame header is always 7, frame end is 1, content header is 12 + props
        return 20 + self.properties.get_size()


class AMQPBodyFrame(AMQPFrame):
    FRAME_TYPE = FRAME_BODY

    FRAME_SIZE_WITHOUT_PAYLOAD = 8

    def __init__(self, channel, data):
        """
        :type data: binary
        """
        AMQPFrame.__init__(self, channel)
        assert isinstance(data, (six.binary_type, buffer, memoryview))
        self.data = data

    def write_to(self, buf):
        buf.write(struct.pack('!BHL', FRAME_BODY, self.channel, len(self.data)))
        buf.write(self.data)
        buf.write(chr(FRAME_END))

    @staticmethod
    def unserialize(channel, payload_as_buffer):
        return AMQPBodyFrame(channel, payload_as_buffer)

    def get_size(self):
        return 8 + len(self.data)


class AMQPHeartbeatFrame(AMQPFrame):
    FRAME_TYPE = FRAME_HEARTBEAT
    LENGTH = 8
    DATA = struct.pack('!BHLB', FRAME_HEARTBEAT, 0, 0, FRAME_END)

    def __init__(self):
        AMQPFrame.__init__(self, 0)

    def write_to(self, buf):
        buf.write(AMQPHeartbeatFrame.DATA)

    def get_size(self):
        return AMQPHeartbeatFrame.LENGTH