#coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
import six

from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, \
    ConnectionDown, ConsumerCancelled, Message


def getamqp():
    amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
    amqp.start()
    return amqp


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.amqp = getamqp()
        self.assertIsInstance(self.amqp.drain(1), ConnectionUp)

    def tearDown(self):
        self.amqp.shutdown()

    def test_acknowledge(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.send(Message('what the fuck'), '', routing_key='myqueue')

        p = self.amqp.drain(wait=4)
        self.assertIsInstance(p, MessageReceived)
        self.assertEquals(p.message.body, 'what the fuck')
        p.message.ack()

        self.assertIs(self.amqp.drain(wait=4), None)

    def test_nacknowledge(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.send(Message('what the fuck'), '', routing_key='myqueue')

        p = self.amqp.drain(wait=4)
        self.assertIsInstance(p, MessageReceived)
        self.assertEquals(p.message.body, 'what the fuck')
        p.message.nack()

        p = self.amqp.drain(wait=4)
        self.assertIsInstance(p, MessageReceived)
        self.assertEquals(six.binary_type(p.message.body), 'what the fuck')


    def test_bug_hangs(self):
        p = Queue('lol', exclusive=True)
        self.amqp.consume(p)
        self.amqp.consume(p).result()

    def test_consume_twice(self):
        """Spawn a second connection and try to consume an exclusive queue twice"""
        amqp2 = getamqp()

        has_failed = {'has_failed': False}

        self.amqp.consume(Queue('lol', exclusive=True)).result()
        amqp2.consume(Queue('lol', exclusive=True), on_failed=lambda e: has_failed.update({'has_failed': True})).result()

        self.assertTrue(has_failed['has_failed'])

        amqp2.shutdown()

    def test_send_and_receive(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.send(Message('what the fuck'), '', routing_key='myqueue')

        p = self.amqp.drain(wait=10)
        self.assertIsInstance(p, MessageReceived)
        self.assertEquals(p.message.body, 'what the fuck')

    def test_consumer_cancelled_on_queue_deletion(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.delete_queue(myq)

        self.assertIsInstance(self.amqp.drain(wait=10), ConsumerCancelled)

    def test_consumer_cancelled_on_consumer_cancel(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.cancel(myq)

        self.assertIsInstance(self.amqp.drain(wait=10), ConsumerCancelled)
