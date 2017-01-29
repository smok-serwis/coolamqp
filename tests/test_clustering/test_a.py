# coding=UTF-8
"""
Test things
"""
from __future__ import print_function, absolute_import, division
import six
import unittest
import time, logging, threading, monotonic
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, ReceivedMessage, Exchange
from coolamqp.clustering import Cluster, MessageReceived, NothingMuch

import time

NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestA(unittest.TestCase):

    def setUp(self):
        self.c = Cluster([NODE])
        self.c.start()

    def tearDown(self):
        self.c.shutdown()

    def test_delete_queue(self):
        # that's how it's written, due to http://www.rabbitmq.com/specification.html#method-status-queue.delete
        self.c.delete_queue(Queue(u'i-do-not-exist')).result()

    def test_consume(self):
        con, fut = self.c.consume(Queue(u'hello', exclusive=True))
        fut.result()
        con.cancel()

    def test_actually_waits(self):
        a = monotonic.monotonic()

        self.c.drain(5)

        self.assertTrue(monotonic.monotonic() - a >= 4)


    def test_set_qos_but_later(self):
        con, fut = self.c.consume(Queue(u'hello', exclusive=True))

        fut.result()

        con.set_qos(100, 100)
        time.sleep(1)
        self.assertEquals(con.qos, (100, 100))

        con.set_qos(None, 110)
        time.sleep(1)
        self.assertEquals(con.qos, (0, 110))


    def test_anonymq(self):
        q = Queue(exchange=Exchange(u'ooo', type=b'fanout', auto_delete=True), auto_delete=True)

        c, f = self.c.consume(q)

        f.result()

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

    def test_message_with_propos_confirm(self):

        P = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            self.assertEquals(e.body, b'hello')
            #bcoz u can compare memoryviews to their providers :D
            self.assertEquals(e.properties.content_type, b'text/plain')
            self.assertEquals(e.properties.content_encoding, b'utf8')
            P['q'] = True

        con, fut = self.c.consume(Queue(u'hello', exclusive=True), on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b'hello', properties={
            'content_type': b'text/plain',
            'content_encoding': b'utf8'
        }), routing_key=u'hello', confirm=True).result()

        self.assertRaises(RuntimeError, lambda: self.c.publish(Message(b'hello', properties={
            'content_type': b'text/plain',
            'content_encoding': b'utf8'
        }), routing_key=u'hello', confirm=True, tx=True).result())

        time.sleep(1)

        self.assertTrue(P['q'])

    def test_message_with_propos(self):

        P = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            self.assertEquals(e.body, b'hello')
            #bcoz u can compare memoryviews to their providers :D
            self.assertEquals(e.properties.content_type, b'text/plain')
            self.assertEquals(e.properties.content_encoding, b'utf8')
            P['q'] = True

        con, fut = self.c.consume(Queue(u'hello', exclusive=True), on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b'hello', properties={
            'content_type': b'text/plain',
            'content_encoding': b'utf8'
        }), routing_key=u'hello', tx=True).result()

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


    def test_consumer_cancel(self):
        con, fut = self.c.consume(Queue(u'hello', exclusive=True, auto_delete=True))
        fut.result()
        con.cancel().result()

    def test_drain_1(self):
        con, fut = self.c.consume(Queue(u'hello', exclusive=True, auto_delete=True))
        fut.result()

        self.c.publish(Message(b'ioi'), routing_key=u'hello')

        self.assertIsInstance(self.c.drain(2), MessageReceived)
        self.assertIsInstance(self.c.drain(1), NothingMuch)
