import logging
import time
import os
import unittest
import logging
import uuid

import monotonic

from coolamqp.clustering import Cluster
from coolamqp.objects import Exchange, Queue, NodeDefinition, Message, MessageProperties


XCHG = Exchange('smok5.results', type='topic', durable=True)
QUEUE = Queue('', exchange=XCHG, exclusive=True, auto_delete=True)
logger = logging.getLogger(__name__)

NODE = NodeDefinition(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('coolamqp').setLevel(logging.DEBUG)

did_receive = False


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

    def test_headers_exchange(self):
        xchg_name = uuid.uuid4().hex
        exchange = Exchange(xchg_name, b'headers')
        self.c.declare(exchange).result()
        queue1 = Queue(uuid.uuid4().hex, exchange=exchange, arguments_bind={'x-match': 'all', 'location': 'brisbane'})
        self.c.declare(queue1).result()
        queue2 = Queue(uuid.uuid4().hex, exchange=exchange, arguments_bind={'x-match': 'all', 'location': 'sydney'})
        self.c.declare(queue2).result()

        test = {'a': 0}

        def do_message(msg):
            msg.ack()
            test['a'] += 1

        cons1, fut1 = self.c.consume(queue1, on_message=do_message, no_ack=False)
        cons2, fut2 = self.c.consume(queue2, on_message=do_message, no_ack=False)
        fut1.result()
        fut2.result()

        self.c.publish(Message(b'dupa', MessageProperties(headers={'location': 'sydney'})), exchange=exchange, confirm=True).result()
        self.c.publish(Message(b'dupa', MessageProperties(headers={'location': 'brisbane'})), exchange=exchange, confirm=True).result()
        self.c.publish(Message(b'dupa', MessageProperties(headers={'location': 'wtf'})), exchange=exchange, confirm=True).result()
        time.sleep(1)
        cons1.cancel().result()
        cons2.cancel().result()
        self.assertEqual(test['a'], 2)

    def test_bind_stuff(self):
        self.c.declare(QUEUE)
        self.c.declare(XCHG).result()
        self.c.bind(QUEUE, XCHG, routing_key='hello-world').result()
        global did_receive

        def do(msg):
            global did_receive
            if msg.body == b'good boy':
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
        self.c.publish(Message(b'good boy2'), exchange=XCHG, routing_key='yolooldies', confirm=True).result()
        time.sleep(10)
        self.assertFalse(did_receive)
