#coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest

from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, \
    ConnectionDown, ConsumerCancelled, Message


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
        self.amqp.start()
        self.assertIsInstance(self.amqp.drain(1), ConnectionUp)

    def tearDown(self):
        self.amqp.shutdown()

    def test_send_and_receive(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        p = self.amqp.drain(wait=10)
        self.assertIsInstance(p, MessageReceived)
        self.assertEquals(p.message.body, b'what the fuck')

#    def test_consumer_cancelled_on_queue_deletion(self):
#        myq = Queue('myqueue', exclusive=True)
#
#        self.amqp.consume(myq)
#        self.amqp.delete_queue(myq)
#
#        self.assertIsInstance(self.amqp.drain(wait=10), ConsumerCancelled)

    def test_consumer_cancelled_on_consumer_cancel(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.cancel(myq)

        self.assertIsInstance(self.amqp.drain(wait=10), ConsumerCancelled)

        self.amqp.delete_queue(myq)
