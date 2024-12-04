# coding=UTF-8

from __future__ import print_function, absolute_import, division

import logging
import os
import time
import unittest

from coolamqp.clustering import Cluster
from coolamqp.exceptions import ConnectionDead
from coolamqp.objects import NodeDefinition, Queue, Exchange, Message

NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', heartbeat=20)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('coolamqp').setLevel(logging.DEBUG)


class TestStreams(unittest.TestCase):

    def test_streams(self):
        c = Cluster(NODE)
        c.start(wait=True, timeout=None)
        if not c.properties.properties['version'].startswith('4'):
            c.shutdown(wait=True)
            return

        stream = Queue('my-stream', durable=True, auto_delete=False, exclusive=False,
                       arguments={'x-queue-type': 'stream'})
        c.declare(stream).result()

        for i in range(10):
            c.publish(Message(('dupa%s' % (i, )).encode('utf-8')), routing_key='my-stream', confirm=True).result()

        test = {'a': 0}

        def handle_msg(msg):
            test['a'] += 1
            msg.ack()

        cons, fut = c.consume(stream, qos=10, on_message=handle_msg, arguments={'x-stream-offset': 4}, no_ack=False)
        fut.result()
        time.sleep(3)
        cons.cancel().result()
        self.assertGreaterEqual(test['a'], 6)       # might have some messages from previous runs
        cons, fut = c.consume(stream, qos=10, on_message=handle_msg, arguments={'x-stream-offset': 'first'}, no_ack=False)
        fut.result()
        time.sleep(3)
        cons.cancel()
        self.assertGreaterEqual(test['a'], 16)       # might have some messages from previous runs
