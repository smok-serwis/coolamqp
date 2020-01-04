# coding=UTF-8
from __future__ import print_function, absolute_import, division

import unittest

from coolamqp.exceptions import AMQPError


class TestExcs(unittest.TestCase):
    def test_exist(self):
        e = AMQPError(100, u'wtf', 0, 0)

        self.assertTrue(u'100' in str(e))
        self.assertTrue(u'wtf' in str(e))
        self.assertTrue(repr(e).startswith(u'AMQPError'))

    def test_parses_memoryview_correctly(self):
        e = AMQPError(100, memoryview(u'wtf'.encode('utf8')), 0, 0)
        self.assertIn('wtf', str(e))
        self.assertIn('wtf', repr(e))
