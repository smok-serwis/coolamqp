import io
import unittest

from coolamqp.framing.field_table import enframe_table

from coolamqp.objects import argumentify


class TestFraming(unittest.TestCase):
    def test_enframing_arguments(self):
        buf = io.BytesIO()
        args = argumentify({'x-match': 'all', 'format': 'pdf'})
        enframe_table(buf, args)
