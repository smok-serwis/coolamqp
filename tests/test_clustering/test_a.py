# coding=UTF-8
"""
Test things
"""
from __future__ import print_function, absolute_import, division
import six
import unittest
import time, logging, threading
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue
from coolamqp.clustering import Cluster

import time


NODE = NodeDefinition('127.0.0.1', 'user', 'user', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestA(unittest.TestCase):
    def test_link(self):
        """Connect and disconnect"""
        c = Cluster([NODE])
        c.start()
        c.shutdown()

    def test_consume(self):
        c = Cluster([NODE])
        c.start()
        con, fut = c.consume(Queue(u'hello', exclusive=True))
#        fut.result()
        con.cancel()
        c.shutdown()


