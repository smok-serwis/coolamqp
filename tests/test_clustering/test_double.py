# coding=UTF-8
"""
Double trouble!
"""
from __future__ import print_function, absolute_import, division
import six
import unittest
import time, logging, threading
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, ReceivedMessage
from coolamqp.clustering import Cluster
NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)


class TestDouble(unittest.TestCase):

    def setUp(self):
        self.c1 = Cluster([NODE])
        self.c1.start()

        self.c2 = Cluster([NODE])
        self.c2.start()

    def tearDown(self):
        self.c1.shutdown()
        self.c2.shutdown()

    def test_resource_locked(self):

        q = Queue(u'yo', exclusive=True, auto_delete=True)

        con, fut = self.c1.consume(q)
        fut.result()

        con2, fut2 = self.c2.consume(q, fail_on_first_time_resource_locked=True)

        from coolamqp.exceptions import ResourceLocked

        self.assertRaises(ResourceLocked, lambda: fut2.result())

        
