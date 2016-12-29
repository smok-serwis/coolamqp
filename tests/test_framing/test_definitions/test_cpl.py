# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
import io


from coolamqp.framing.definitions import BasicContentPropertyList


class TestBasicContentPropertyList(unittest.TestCase):
    def test_bcpl1(self):
        bcpl = BasicContentPropertyList(content_type='text/plain', content_encoding='utf8')

        self.assertEquals(bcpl.content_type, 'text/plain')
        self.assertEquals(bcpl.content_encoding, 'utf8')

        buf = io.BytesIO()
        bcpl.write_to(buf)

        ser = buf.getvalue()
        self.assertEquals(ser, '\xC0\x00' + chr(len('text/plain')) + b'text/plain\x04utf8')

    def test_bcpl2(self):
        bcpl = BasicContentPropertyList(content_type='text/plain')

        self.assertEquals(bcpl.content_type, 'text/plain')

        buf = io.BytesIO()
        bcpl.write_to(buf)

        ser = buf.getvalue()
        self.assertEquals(ser, '\x80\x00' + chr(len('text/plain')) + b'text/plain')
