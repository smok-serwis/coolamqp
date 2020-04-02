# coding=UTF-8
"""
Concrete frame definitions
"""
from __future__ import absolute_import, division, print_function

import struct

import six

from coolamqp.framing.base import AMQPFrame
from coolamqp.framing.definitions import FRAME_METHOD, FRAME_HEARTBEAT, \
    FRAME_BODY, FRAME_HEADER, FRAME_END, \
    IDENT_TO_METHOD, CLASS_ID_TO_CONTENT_PROPERTY_LIST, FRAME_END_BYTE

STRUCT_BH = struct.Struct('!BH')
STRUCT_BHL = struct.Struct('!BHL')
STRUCT_HH = struct.Struct('!HH')
STRUCT_BHLHHQ = struct.Struct('!BHLHHQ')
STRUCT_HHQ = struct.Struct('!HHQ')
STRUCT_BHLB = struct.Struct('!BHLB')


class AMQPMethodFrame(AMQPFrame):
    FRAME_TYPE = FRAME_METHOD

    def __init__(self, channel, payload):
        # type: (int, coolamqp.framing.base.AMQPMethodPayload) -> None
        """
        :param channel: channel ID
        :param payload: AMQPMethodPayload instance
        """
        AMQPFrame.__init__(self, channel)
        self.payload = payload

    def __str__(self):  # type: () -> str
        return 'AMQPMethodFrame(%s, %s)' % (self.channel, self.payload)

    def write_to(self, buf):
        if self.payload.IS_CONTENT_STATIC:
            buf.write(STRUCT_BH.pack(FRAME_METHOD, self.channel))
            buf.write(self.payload.STATIC_CONTENT)
        else:
            buf.write(STRUCT_BHL.pack(FRAME_METHOD, self.channel,
                                      4 + self.payload.get_size()))
            buf.write(self.payload.BINARY_HEADER)
            self.payload.write_arguments(buf)
            buf.write(FRAME_END_BYTE)

    @classmethod
    def unserialize(cls, channel, payload_as_buffer):
        clsmet = STRUCT_HH.unpack_from(payload_as_buffer, 0)

        try:
            method_payload_class = IDENT_TO_METHOD[clsmet]
            payload = method_payload_class.from_buffer(payload_as_buffer, 4)
        except KeyError:
            raise ValueError('Invalid class %s method %s' % clsmet)
        else:
            return cls(channel, payload)

    def get_size(self):  # type: () -> int
        # frame_header = (method(1) + channel(2) + length(4) + class(2) + method(2) + payload(N) + frame_end(1))
        return 12 + self.payload.get_size()


class AMQPHeaderFrame(AMQPFrame):
    """
    A frame containing a message header

    :param channel: channel ID
    :type channel: int
    :param class_id: class ID
    :type class_id: int
    :param weight: weight (lol wut?)
    :param body_size: size of the body to follow
    :param properties: a suitable AMQPContentPropertyList instance
    """
    FRAME_TYPE = FRAME_HEADER

    def __init__(self, channel, class_id, weight, body_size, properties):
        AMQPFrame.__init__(self, channel)
        self.class_id = class_id
        self.weight = weight
        self.body_size = body_size
        self.properties = properties

    def write_to(self, buf):
        buf.write(STRUCT_BHLHHQ.pack(FRAME_HEADER, self.channel,
                                     12 + self.properties.get_size(), self.class_id,
                                     0,
                                     self.body_size))
        self.properties.write_to(buf)
        buf.write(FRAME_END_BYTE)

    @staticmethod
    def unserialize(channel, payload_as_buffer):
        # payload starts with class ID
        class_id, weight, body_size = STRUCT_HHQ.unpack_from(payload_as_buffer, 0)
        properties = CLASS_ID_TO_CONTENT_PROPERTY_LIST[class_id].from_buffer(
            payload_as_buffer, 12)
        return AMQPHeaderFrame(channel, class_id, weight, body_size,
                               properties)

    def get_size(self):  # type: () -> int
        # frame header is always 7, frame end is 1, content header is 12 + props
        return 20 + self.properties.get_size()

    def __str__(self):  # type: () -> str
        return 'AMQPHeaderFrame(%s, %s, %s, %s, %s)' % (self.channel, self.class_id, self.weight,
                                                        self.body_size, self.properties)


class AMQPBodyFrame(AMQPFrame):
    """
    A frame containing message body

    :param channel: Channel ID
    :type channel: int
    :param data: body (or a piece of it) of a message
    :type data: binary
    """

    FRAME_TYPE = FRAME_BODY

    FRAME_SIZE_WITHOUT_PAYLOAD = 8

    def __init__(self, channel, data):  # type: (int, bytes) -> None
        AMQPFrame.__init__(self, channel)
        assert isinstance(data, (six.binary_type, memoryview))
        self.data = data

    def write_to(self, buf):
        buf.write(
            STRUCT_BHL.pack(FRAME_BODY, self.channel, len(self.data)))
        buf.write(self.data)
        buf.write(FRAME_END_BYTE)

    @classmethod
    def unserialize(cls, channel, payload_as_buffer):
        return cls(channel, payload_as_buffer)

    def get_size(self):  # type: () -> int
        return 8 + len(self.data)

    def __str__(self):  # type: () -> str
        return '<AMQPBodyFrame of size %s>' % (len(self.data),)


class AMQPHeartbeatFrame(AMQPFrame):
    FRAME_TYPE = FRAME_HEARTBEAT
    LENGTH = 8
    DATA = STRUCT_BHLB.pack(FRAME_HEARTBEAT, 0, 0, FRAME_END)

    def __init__(self):
        AMQPFrame.__init__(self, 0)

    def write_to(self, buf):
        buf.write(AMQPHeartbeatFrame.DATA)

    def get_size(self):
        return AMQPHeartbeatFrame.LENGTH

    def __str__(self):
        return 'AMQPHeartbeatFrame()'
