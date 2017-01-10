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

#todo handle bad auth
NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)
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

    def test_send_recv_zerolen(self):

        P = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            P['q'] = True

        con, fut = self.c.consume(Queue(u'hello', exclusive=True), on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b''), routing_key=u'hello', tx=True).result()

        time.sleep(1)

        self.assertTrue(P['q'])

    def test_send_recv_nonzerolen(self):

        P = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            self.assertEquals(e.body, b'hello')
            P['q'] = True

        con, fut = self.c.consume(Queue(u'hello', exclusive=True), on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b'hello'), routing_key=u'hello', tx=True).result()

        time.sleep(1)

        self.assertTrue(P['q'])

    def test_send_recv_nonzerolen_fuckingmemoryviews(self):

        P = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            self.assertIsInstance(e.body[0], memoryview)
            P['q'] = True

        con, fut = self.c.consume(Queue(u'hello', exclusive=True), on_message=ok, no_ack=True, fucking_memoryviews=True)
        fut.result()
        self.c.publish(Message(b'hello'), routing_key=u'hello', tx=True).result()

        time.sleep(1)

        self.assertTrue(P['q'])
