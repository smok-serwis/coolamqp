# coding=UTF-8

from __future__ import print_function, absolute_import, division
import six
import os
import unittest
import time, logging, threading, monotonic, warnings
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, \
    ReceivedMessage, Exchange
from coolamqp.clustering import Cluster, MessageReceived, NothingMuch
from coolamqp.exceptions import ConnectionDead

import time

NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestConnecting(unittest.TestCase):
    def test_on_fail(self):
        q = {'failed': False}
        c = Cluster(
            NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'xguest', 'xguest', heartbeat=20),
            on_fail=lambda: q.update(failed=True))
        self.assertRaises(ConnectionDead, c.start)
        c.shutdown()
        self.assertTrue(q['failed'])

    def test_on_clean(self):
        q = {'failed': False}
        c = Cluster([NODE], on_fail=lambda: q.update(failed=True))
        c.start(wait=True)
        c.shutdown()
        time.sleep(5)
        self.assertFalse(q['failed'])

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

        self.assertEquals(node.virtual_host, '/')  # default

    def test_amqpconnstring_port(self):
        node = NodeDefinition('amqp://lol:lol@lol:4123/vhost')

        self.assertEquals(node.port, 4123)
