# coding=UTF-8
"""
Test things
"""
from __future__ import print_function, absolute_import, division
import six
import unittest
import time, logging, threading
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, ReceivedMessage
from coolamqp.clustering import Cluster

import time


NODE = NodeDefinition('127.0.0.1', 'user', 'user', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestA(unittest.TestCase):

    def setUp(self):
        self.c = Cluster([NODE])
        self.c.start()

    def tearDown(self):
        self.c.shutdown()

    def test_consume(self):
        con, fut = self.c.consume(Queue(u'hello', exclusive=True))
#        fut.result()
        con.cancel()

    def test_send_recv(self):

        P = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            P['q'] = True

        con, fut = self.c.consume(Queue(u'hello', exclusive=True), on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b''), routing_key=u'hello', tx=True).result()

        time.sleep(1)

        self.assertTrue(P['q'])



