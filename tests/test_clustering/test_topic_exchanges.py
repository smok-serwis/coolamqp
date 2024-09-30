import time
import os
import unittest
import logging

import monotonic

from coolamqp.clustering import Cluster
from coolamqp.objects import Exchange, Queue, NodeDefinition, Message


XCHG = Exchange('smok5.results', type='topic', durable=True)
QUEUE = Queue(exchange=XCHG, exclusive=True, auto_delete=True)


NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestTopic(unittest.TestCase):
    def setUp(self):
        self.c = Cluster([NODE])
        self.c.start()

    def tearDown(self):
        try:
            self.cons.cancel().result()
        except AttributeError:
            pass
        self.c.shutdown()

    def test_bind_stuff(self):
        self.c.declare(XCHG).result()
        self.c.declare(QUEUE).result()
        self.c.bind(QUEUE, XCHG, routing_key='hello-world').result()

        did_receive = False

        def do(msg):
            nonlocal did_receive
            did_receive = True
            msg.ack()

        self.cons, fut = self.c.consume(QUEUE, on_message=do, no_ack=False)
        fut.result()

        self.c.publish(Message(b'good boy'), exchange=XCHG, routing_key='hello-world')

        start = monotonic.monotonic()
        while not did_receive:
            time.sleep(2)
            if monotonic.monotonic() - start > 10:
                self.fail("Message not received within 10 seconds")

        did_receive = False
        self.c.publish(Message(b'good boy', exchange=XCHG, routing_key='helloworld'), confirm=True).result()
        time.sleep(5)
        self.assertFalse(did_receive)
