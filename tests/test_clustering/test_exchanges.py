# coding=UTF-8
from __future__ import print_function, absolute_import, division
import six
import unittest
import os
import time, logging, threading
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, \
    ReceivedMessage, Exchange
from coolamqp.clustering import Cluster, MessageReceived, NothingMuch
from coolamqp.exceptions import AMQPError
import time

# todo handle bad auth
NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestExchanges(unittest.TestCase):
    def setUp(self):
        self.c = Cluster([NODE])
        self.c.start()

    def tearDown(self):
        self.c.shutdown()

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

        self.c.publish(Message(b'hello'), exchange=x, tx=True).result()

        self.assertIsInstance(self.c.drain(2), MessageReceived)
        self.assertIsInstance(self.c.drain(2), MessageReceived)
        self.assertIsInstance(self.c.drain(2), NothingMuch)
