# coding=UTF-8

from __future__ import print_function, absolute_import, division

import logging
import os
import time
import unittest

from coolamqp.clustering import Cluster
from coolamqp.exceptions import ConnectionDead
from coolamqp.objects import NodeDefinition, Queue, Exchange

NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('coolamqp').setLevel(logging.DEBUG)


class TestConnecting(unittest.TestCase):

    def test_argumented_exchange(self):
        xchg = Exchange('test-wer', durable=True)
        c = Cluster([NODE])
        c.start(wait=True, timeout=None)
        c.declare(xchg).result()
        xchg2 = Exchange('test2-werwer', durable=True, arguments={'alternate-exchange': 'test-wer'})
        c.declare(xchg2).result()
        c.shutdown(True)

    def test_argumented_queue(self):
        que = Queue(auto_delete=True, exclusive=True, arguments=[(b'x-max-priority', 10)])
        c = Cluster([NODE])
        c.start(wait=True, timeout=None)
        self.assertRaises(ValueError, c.declare, que)
        c.shutdown(True)

    def test_argumented_bind(self):
        c = Cluster([NODE])
        c.start(wait=True, timeout=None)
        que = Queue('', auto_delete=True, exclusive=True, arguments=[(b'x-max-priority', 10)])
        xchg = Exchange('test3-wertest', type='headers', durable=True)
        c.declare(que).result()
        c.declare(xchg).result()
        c.bind(que, xchg, routing_key=b'', arguments={'x-match': 'all', 'format': 'pdf'}).result()
        c.shutdown(True)

    def test_connection_blocked(self):
        try:
            from coolamqp.framing.definitions import ConnectionBlocked
        except ImportError:
            self.skipTest('ConnectionBlocked not supported!')

    def test_wait_timeout_none(self):
        c = Cluster([NODE])
        c.start(wait=True, timeout=None)
        c.shutdown(wait=True)

    def test_on_fail(self):
        """Assert that on_fail doesn't fire if the cluster fails to connect"""
        q = {'failed': False}
        c = Cluster(
            NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'xguest', 'xguest', heartbeat=20),
            on_fail=lambda: q.update(failed=True))
        self.assertRaises(ConnectionDead, c.start)
        c.shutdown()
        self.assertFalse(q['failed'])

    def test_on_clean(self):
        q = {'failed': False}
        c = Cluster([NODE], on_fail=lambda: q.update(failed=True))
        c.start(wait=True)
        c.shutdown()
        time.sleep(5)
        self.assertFalse(q['failed'])

    def test_start_called_multiple_times(self):
        c = Cluster([NODE])
        c.start(wait=True, timeout=20)
        self.assertRaises(RuntimeError, lambda: c.start())
        c.shutdown(wait=True)

    def test_shutdown_without_start(self):
        c = Cluster([NODE])
        self.assertRaises(RuntimeError, lambda: c.shutdown())

    def test_queues_equal_and_hashable(self):
        q1 = Queue(u'lolwut')
        q2 = Queue(b'lolwut')
        q3 = Queue(u'not')

        self.assertEqual(q1, q2)
        self.assertEqual(hash(q1), hash(q2))
        self.assertNotEqual(q1, q3)

    def test_node_with_kwargs(self):
        node = NodeDefinition(host='127.0.0.1',
                              user='guest',
                              password='guest')

        self.assertEqual(node.virtual_host, '/')  # default

    def test_amqpconnstring_port(self):
        node = NodeDefinition('amqp://lol:lol@lol:4123/vhost')

        self.assertEqual(node.port, 4123)
