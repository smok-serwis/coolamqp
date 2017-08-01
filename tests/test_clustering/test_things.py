# coding=UTF-8

from __future__ import print_function, absolute_import, division
import six
import unittest
import time, logging, threading, monotonic, warnings
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, ReceivedMessage, Exchange
from coolamqp.clustering import Cluster, MessageReceived, NothingMuch

import time
NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestConnecting(unittest.TestCase):

    def test_reconnect(self):
        c = Cluster([NodeDefinition('8.8.8.8', 'invalid', 'invalid', heartbeat=10),
                     NODE])
        c.start(wait=True)
        con, fut = c.consume(Queue(u'hello', exclusive=True))
        fut.result()
        con.cancel()

    def test_start_called_multiple_times(self):
        c = Cluster([NODE])
        c.start(wait=True)
        self.assertRaises(RuntimeError, lambda: c.start())
        c.shutdown(wait=True)

    def test_shutdown_without_start(self):
        c = Cluster([NODE])
        self.assertRaises(RuntimeError, lambda: c.shutdown())

    def test_queues_equal_and_hashable(self):
        q1 = Queue(u'lolwut')
        q2 = Queue(b'lolwut')
        q3 = Queue(u'not')

        self.assertEquals(q1, q2)
        self.assertEquals(hash(q1), hash(q2))
        self.assertNotEqual(q1, q3)

    def test_node_with_kwargs(self):
        node = NodeDefinition(host='127.0.0.1',
                              user='guest',
                              password='guest')

        self.assertEquals(node.virtual_host, '/')   # default

    def test_amqpconnstring_port(self):
        node = NodeDefinition('amqp://lol:lol@lol:4123/vhost')

        self.assertEquals(node.port, 4123)
