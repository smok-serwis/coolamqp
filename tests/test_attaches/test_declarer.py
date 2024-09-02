import unittest

from coolamqp.attaches import Declarer


class TestDeclarer(unittest.TestCase):
    def test_declarer_slots(self):
        """Test that __slots__ are respected"""
        d = Declarer(None)
        def add_argument():
            d.extra_argument = False

        self.assertRaises(AttributeError, add_argument)
