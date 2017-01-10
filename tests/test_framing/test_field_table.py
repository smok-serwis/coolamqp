# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
import struct
import io
import six

from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size, \
                                         enframe_field_value, deframe_field_value, frame_field_value_size


if six.PY3:
    buffer = memoryview

class TestFramingTables(unittest.TestCase):
    def test_frame_unframe_table(self):

        tab = [
                (b'field', (b'yo', b's'))
            ]

        buf = io.BytesIO()

        self.assertEquals(frame_table_size(tab), 4+6+4)

        enframe_table(buf, tab)
        buf = buf.getvalue()

        self.assertEquals(buf, struct.pack('!I', 10) + b'\x05fields\x02yo')

        tab, delta = deframe_table(buffer(buf), 0)

        self.assertEquals(len(tab), 1)
        self.assertEquals(delta, 14)
        self.assertEquals(tab[0], (b'field', (b'yo', b's')))

    def test_frame_unframe_value(self):

        buf = io.BytesIO()

        enframe_field_value(buf, (b'yo', b's'))

        buf = buf.getvalue()
        self.assertEquals(b's\x02yo', buf)

        fv, delta = deframe_field_value(buffer(buf), 0)
        self.assertEquals(fv, (b'yo', b's'))
        self.assertEquals(delta, 4)

        self.assertEquals(frame_field_value_size(fv), 4)
