# coding=UTF-8
from __future__ import print_function, absolute_import, division

import logging
import os
import time
import unittest
import uuid

from coolamqp.clustering import Cluster, MessageReceived, NothingMuch
from coolamqp.objects import Message, NodeDefinition, Queue, MessageProperties, Exchange

# todo handle bad auth
NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', hertbeat=20)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('coolamqp').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class TestExchanges(unittest.TestCase):
    def setUp(self):
        self.c = Cluster([NODE])
        self.c.start()

    def tearDown(self):
        self.c.shutdown()

    def test_declare_anonymq(self):
        que = Queue(auto_delete=True)
        self.assertRaises(ValueError, self.c.declare, que)
        cons, fut = self.c.consume(que, no_ack=True)
        fut.result()
        cons.cancel().result()

    def test_topic_exchanges(self):
        xchg_name = uuid.uuid4().hex
        test = {'a': 0}

        def do_msg(msg):
            msg.ack()
            test['a'] += 1

        xchg = Exchange(xchg_name, type=b'topic')
        queue = Queue(exchange=xchg, routing_key=b'test')
        cons, fut = self.c.consume(queue, no_ack=False, on_message=do_msg)
        fut.result()
        self.c.publish(Message(b'dupa'), xchg_name, routing_key=b'test', confirm=True).result()
        self.c.publish(Message(b'dupa2'), xchg_name, routing_key=b'test2', confirm=True).result()
        self.c.publish(Message(b'dupa'), xchg_name, routing_key=b'test', confirm=True).result()
        time.sleep(1)
        cons.cancel().result()
        self.assertEqual(test['a'], 2)

    def test_deadlettering(self):
        xchg_name = uuid.uuid4().hex
        dead_queue_name = uuid.uuid4().hex
        grave_queue_name = uuid.uuid4().hex
        DEADLETTER = Exchange(xchg_name, type=b'direct')
        QUEUE = Queue(dead_queue_name, durable=True, auto_delete=False, exclusive=False)
        GRAVEYARD_QUEUE = Queue(grave_queue_name, durable=True, auto_delete=False, arguments={'x-dead-letter-exchange': xchg_name,
                                           'x-message-ttl': 1000})
        self.c.declare(DEADLETTER).result()
        self.c.declare(QUEUE).result()
        self.c.declare(GRAVEYARD_QUEUE).result()
        self.c.bind(QUEUE, DEADLETTER, grave_queue_name).result()
        cons, fut = self.c.consume(QUEUE, no_ack=True)
        fut.result()
        self.c.publish(Message(b'test', MessageProperties(content_type=b'application/json',
                              content_encoding=b'utf8',
                              delivery_mode=2)), routing_key=grave_queue_name, confirm=True).result()

        self.assertIsInstance(self.c.drain(10), MessageReceived)
        cons.cancel()

    def test_declare_exchange(self):
        a = Exchange(u'jolax', type=b'fanout', auto_delete=True)
        self.c.declare(a).result()

    def test_fanout(self):
        x = Exchange(u'jola', type='direct', auto_delete=True)

        c1, f1 = self.c.consume(Queue('one', exchange=x, exclusive=True),
                                no_ack=True)
        c2, f2 = self.c.consume(Queue('two', exchange=x, exclusive=True),
                                no_ack=True)

        f1.result()
        f2.result()

        self.c.publish(Message(b'hello'), exchange=x, confirm=True).result()

        self.assertIsInstance(self.c.drain(2), MessageReceived)
        self.assertIsInstance(self.c.drain(2), MessageReceived)
        self.assertIsInstance(self.c.drain(2), NothingMuch)
