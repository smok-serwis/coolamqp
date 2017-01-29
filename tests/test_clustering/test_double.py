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
from coolamqp.exceptions import AMQPError, RESOURCE_LOCKED


logging.basicConfig(level=logging.DEBUG)


class TestDouble(unittest.TestCase):

    def setUp(self):
        self.c1 = Cluster([NODE])
        self.c1.start()

        self.c2 = Cluster([NODE])
        self.c2.start()

    def tearDown(self):
        self.c1.shutdown()
        self.c2.shutdown()

    # def test_ccn(self):
    #     q1 = Queue(b'yo', auto_delete=True)
    #
    #     con1, fut1 = self.c1.consume(q1)
    #     fut1.result()
    #
    #     self.c2.delete_queue(q1) #.result()
    #
    #     time.sleep(5)
    #     self.assertTrue(con1.cancelled)
    #
    def test_resource_locked(self):

        q = Queue(u'yo', exclusive=True, auto_delete=True)

        con, fut = self.c1.consume(q, qos=(None, 20))
        fut.result()

        try:
            con2, fut2 = self.c2.consume(q, fail_on_first_time_resource_locked=True)
            fut2.result()
        except AMQPError as e:
            self.assertEquals(e.reply_code, RESOURCE_LOCKED)
            self.assertFalse(e.is_hard_error())
        else:
            self.fail('Expected exception')
