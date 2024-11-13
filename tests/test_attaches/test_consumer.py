# coding=UTF-8
from __future__ import print_function, absolute_import, division

import unittest

from coolamqp.attaches import Consumer
from coolamqp.objects import Queue


class TestConsumer(unittest.TestCase):
    def test_issue_26(self):
        """Support for passing qos as int"""
        cons = Consumer(Queue('wtf'), lambda msg: None, qos=25)
        self.assertEqual(cons.qos, 25)
