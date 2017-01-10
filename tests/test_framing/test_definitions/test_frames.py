# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
import io
import struct
import six
from coolamqp.framing.frames import AMQPHeaderFrame
from coolamqp.framing.definitions import BasicContentPropertyList, FRAME_HEADER, FRAME_END, ConnectionStartOk


class TestShitSerializesRight(unittest.TestCase):

    def test_unser_header_frame(self):
        s = b'\x00\x3C\x00\x00' + \
            b'\x00\x00\x00\x00\x00\x00\x00\x0A' + \
            b'\xC0\x00\x0Atext/plain\x04utf8'

        hf = AMQPHeaderFrame.unserialize(0, memoryview(s))

        self.assertEquals(hf.class_id, 60)
        self.assertEquals(hf.weight, 0)
        self.assertEquals(hf.body_size, 10)
        self.assertEquals(hf.properties.content_type, b'text/plain')
        self.assertEquals(hf.properties.content_encoding, b'utf8')

    def test_ser_header_frame(self):

        a_cpl = BasicContentPropertyList(content_type='text/plain')

        # content_type has len 10

        buf = io.BytesIO()

        hdr = AMQPHeaderFrame(0, 60, 0, 0, a_cpl)
        hdr.write_to(buf)

        s = b'\x00\x3C\x00\x00' + \
            b'\x00\x00\x00\x00\x00\x00\x00\x00' + \
            b'\x80\x00\x0Atext/plain'

        s = chr(FRAME_HEADER) + b'\x00\x00' + \
                  struct.pack('!L', len(s)) + s + chr(FRAME_END)

        self.assertEquals(buf.getvalue(), s)


