# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
import six
import os

from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, ConnectionDown, ConsumerCancelled, Message, Exchange



class TestNoAcknowledge(unittest.TestCase):
    def setUp(self):
        self.amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
        self.amqp.start()
        self.assertIsInstance(self.amqp.drain(1), ConnectionUp)

    def tearDown(self):
        self.amqp.shutdown()

    def test_noack_works(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.qos(0,1 )

        self.amqp.consume(myq, no_ack=True)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.assertIsInstance(self.amqp.drain(wait=1), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)

    def test_noack_works_after_restart(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.qos(0,1 )

        self.amqp.consume(myq, no_ack=True)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.assertIsInstance(self.amqp.drain(wait=1), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)

        os.system("sudo service rabbitmq-server restart")
        self.assertIsInstance(self.amqp.drain(wait=5), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=5), ConnectionUp)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.assertIsInstance(self.amqp.drain(wait=1), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)


    def test_noack_coexists(self):
        myq = Queue('myqueue', exclusive=True)
        my2 = Queue('myqueue2', exclusive=True)

        self.amqp.qos(0, 1)

        self.amqp.consume(myq, no_ack=True)
        self.amqp.consume(my2)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue2')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue2')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue2')

        our_message = None
        for i in range(4):
            mer = self.amqp.drain(wait=1)
            self.assertIsInstance(mer, MessageReceived)
            if mer.message.routing_key == 'myqueue2':
                self.assertIsNone(our_message)
                our_message = mer

        # Should receive nothing, since not acked
        self.assertIsNone(self.amqp.drain(wait=2))

        # ack and receive
        our_message.message.ack()
        mer = self.amqp.drain(wait=1)       # 2nd
        self.assertIsInstance(mer, MessageReceived)
        mer.message.ack()
        mer = self.amqp.drain(wait=1)       # 3rd
        self.assertIsInstance(mer, MessageReceived)
        mer.message.ack()
