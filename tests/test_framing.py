import io
import unittest

from coolamqp.framing.field_table import enframe_table

from coolamqp.objects import argumentify


class TestFraming(unittest.TestCase):
    def test_something(self):
        buf = io.BytesIO()
        args = argumentify({'x-match': 'all', 'format': 'pdf'})
        res = enframe_table(buf, args)
        print(repr(res))
