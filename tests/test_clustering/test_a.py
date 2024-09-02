# coding=UTF-8
"""
Test things
"""
from __future__ import print_function, absolute_import, division

import logging
import os
import time
import unittest

import six

from coolamqp.clustering import Cluster, MessageReceived, NothingMuch
from coolamqp.objects import Message, NodeDefinition, Queue, \
    ReceivedMessage, Exchange
from coolamqp.utils import monotonic

NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestA(unittest.TestCase):
    def setUp(self):
        self.c = Cluster([NODE])
        self.c.start()

    def tearDown(self):
        self.c.shutdown()

    def test_queue_bind(self):
        queue = Queue('my-queue')
        exchange = Exchange('my-exchange', type='topic')
        self.c.declare(queue).result()
        self.c.declare(exchange).result()
        self.c.bind(queue, exchange, 'test').result()
        q = six.moves.queue.Queue()
        cons, fut = self.c.consume(queue, on_message=lambda msg: q.put(msg), no_ack=True)
        fut.result()
        self.c.publish(Message(b'test'), exchange=exchange, routing_key='test', confirm=True).result()
        msg_v = q.get(block=True, timeout=5)
        self.assertEqual(msg_v.body, b'test')
        cons.cancel()

    def test_delete_queue(self):
        # that's how it's written, due to http://www.rabbitmq.com/specification.html#method-status-queue.delete
        self.c.delete_queue(Queue(u'i-do-not-exist')).result()

    def test_consume(self):
        con, fut = self.c.consume(Queue(u'hello', exclusive=True))
        fut.result()
        con.cancel()

    def test_very_long_messages(self):
        con, fut = self.c.consume(Queue(u'hello', exclusive=True))
        fut.result()

        data = six.binary_type(os.urandom(20 * 1024 * 1024 + 1423))

        self.c.publish(Message(data), routing_key=b'hello',
                       confirm=True).result()

    def test_actually_waits(self):
        a = monotonic()

        self.c.drain(5)

        self.assertGreaterEqual(monotonic() - a, 4)

    def test_set_qos_but_later(self):
        con, fut = self.c.consume(Queue(u'hello2', exclusive=True))

        fut.result()

        con.set_qos(100, 100)
        time.sleep(1)
        self.assertEqual(con.qos, (100, 100))

        con.set_qos(None, 110)
        time.sleep(1)
        self.assertEqual(con.qos, (0, 110))

    def test_declare_anonymous(self):
        xchg = Exchange('wtfzomg', type='fanout')
        q = Queue(exchange=xchg)
        self.c.declare(xchg).result()
        self.c.declare(q).result()
        self.assertTrue(q.name)

    def test_anonymq(self):
        q = Queue(exchange=Exchange(u'ooo', type=b'fanout', auto_delete=True),
                  auto_delete=True)

        c, f = self.c.consume(q)

        f.result()

        self.assertTrue(q.name)

    def test_send_recv_zerolen(self):
        p = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            p['q'] = True

        con, fut = self.c.consume(Queue(u'hello3', exclusive=True),
                                  on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b''), routing_key=u'hello3', tx=True).result()

        time.sleep(1)

        self.assertTrue(p['q'])

    def test_nacking_and_acking(self):
        p = {'q': False, 'count': 0}

        def ok(msg):
            if not p['count']:
                msg.nack()
                msg.nack()
            else:
                msg.ack()
                msg.ack()
            self.assertIsInstance(msg, ReceivedMessage)
            p['q'] = True
            p['count'] += 1

        con, fut = self.c.consume(Queue(u'hello3', exclusive=True),
                                  on_message=ok, no_ack=False)
        fut.result()
        self.c.publish(Message(b''), routing_key=u'hello3', tx=True).result()

        time.sleep(1)

        self.assertTrue(p['q'])
        self.assertEqual(p['count'], 2)

    def test_message_with_propos_confirm(self):
        p = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            self.assertEqual(e.body, b'hello4')
            # bcoz u can compare memoryviews to their providers :D
            self.assertEqual(e.properties.content_type, b'text/plain')
            self.assertEqual(e.properties.content_encoding, b'utf8')
            p['q'] = True

        con, fut = self.c.consume(Queue(u'hello4', exclusive=True),
                                  on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b'hello4', properties={
            'content_type': b'text/plain',
            'content_encoding': b'utf8'
        }), routing_key=u'hello4', confirm=True).result()

        self.assertRaises(RuntimeError,
                          lambda: self.c.publish(Message(b'hello4', properties={
                              'content_type': b'text/plain',
                              'content_encoding': b'utf8'
                          }), routing_key=u'hello4', confirm=True,
                                                 tx=True).result())

        time.sleep(1)

        self.assertTrue(p['q'])

    def test_message_with_propos(self):
        p = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            self.assertEqual(e.body, b'hello5')
            # bcoz u can compare memoryviews to their providers :D
            self.assertEqual(e.properties.content_type, b'text/plain')
            self.assertEqual(e.properties.content_encoding, b'utf8')
            p['q'] = True

        con, fut = self.c.consume(Queue(u'hello5', exclusive=True),
                                  on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b'hello5', properties={
            'content_type': b'text/plain',
            'content_encoding': b'utf8'
        }), routing_key=u'hello5', tx=True).result()

        time.sleep(2)

        self.assertTrue(p['q'])

    def test_send_recv_nonzerolen(self):
        """with callback function"""

        p = {'q': False}

        def ok(e):
            self.assertIsInstance(e, ReceivedMessage)
            self.assertEqual(e.body, b'hello6')
            p['q'] = True

        con, fut = self.c.consume(Queue(u'hello6', exclusive=True),
                                  on_message=ok, no_ack=True)
        fut.result()
        self.c.publish(Message(b'hello6'), routing_key=u'hello6',
                       tx=True).result()

        time.sleep(1)

        self.assertTrue(p['q'])

    def test_send_recv_nonzerolen_memoryview(self):
        """single and multi frame in MEMORYVIEW mode"""
        from coolamqp.attaches import BodyReceiveMode

        con, fut = self.c.consume(Queue(u'hello7', exclusive=True), no_ack=True,
                                  body_receive_mode=BodyReceiveMode.MEMORYVIEW)
        fut.result()

        data = b'hello7'
        self.c.publish(Message(data), routing_key=u'hello7', confirm=True)
        m = self.c.drain(2)
        self.assertIsInstance(m, MessageReceived)
        self.assertIsInstance(m.body, memoryview)
        self.assertEqual(m.body, data)

        data = six.binary_type(os.urandom(512 * 1024))
        self.c.publish(Message(data), routing_key=u'hello7', confirm=True)
        m = self.c.drain(9)
        self.assertIsInstance(m, MessageReceived)
        self.assertIsInstance(m.body, memoryview)
        self.assertEqual(m.body.tobytes(), data)

    def test_send_recv_nonzerolen_listofmemoryview(self):
        """single and multi frame in LIST_OF_MEMORYVIEW mode"""
        from coolamqp.attaches import BodyReceiveMode

        con, fut = self.c.consume(Queue(u'hello8', exclusive=True), no_ack=True,
                                  body_receive_mode=BodyReceiveMode.LIST_OF_MEMORYVIEW)
        fut.result()

        data = b'hello8'
        self.c.publish(Message(data), routing_key=u'hello8', confirm=True)
        m = self.c.drain(1)
        self.assertIsInstance(m, MessageReceived)
        self.assertIsInstance(m.body[0], memoryview)
        self.assertEqual(m.body[0], data)

        data = six.binary_type(os.urandom(512 * 1024))
        self.c.publish(Message(data), routing_key=u'hello8', confirm=True)
        m = self.c.drain(5)
        self.assertIsInstance(m, MessageReceived)
        self.assertTrue(all([isinstance(x, memoryview) for x in m.body]))
        self.assertEqual(b''.join(x.tobytes() for x in m.body), data)

    def test_consumer_cancel(self):
        con, fut = self.c.consume(
            Queue(u'hello9', exclusive=True, auto_delete=True))
        fut.result()
        con.cancel().result()

    def test_drain_1(self):
        con, fut = self.c.consume(
            Queue(u'helloA', exclusive=True, auto_delete=True))
        fut.result()

        self.c.publish(Message(b'ioi'), routing_key=u'helloA')

        self.assertIsInstance(self.c.drain(2), MessageReceived)
        self.assertIsInstance(self.c.drain(1), NothingMuch)
