#coding=UTF-8
from __future__ import absolute_import, division, print_function

import unittest
import os
from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, \
    ConnectionDown, ConsumerCancelled, Message


class TestFailures(unittest.TestCase):

    def setUp(self):
        self.amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
        self.amqp.start()
        self.assertIsInstance(self.amqp.drain(1), ConnectionUp)

    def tearDown(self):
        self.amqp.shutdown()

    def test_connection_down_and_up(self):
        """are messages generated at all? does it reconnect?"""
        os.system("sudo service rabbitmq-server restart")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=6), ConnectionUp)

    def test_connection_flags_are_okay(self):
        os.system("sudo service rabbitmq-server stop")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertFalse(self.amqp.connected)
        os.system("sudo service rabbitmq-server start")
        self.assertIsInstance(self.amqp.drain(wait=6), ConnectionUp)
        self.assertTrue(self.amqp.connected)

    def test_connection_down_and_up_redeclare_queues(self):
        """are messages generated at all? does it reconnect?"""

        q1 = Queue('wtf1', exclusive=True)

        self.amqp.consume(q1)

        os.system("sudo service rabbitmq-server restart")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=6), ConnectionUp)

        self.amqp.send(Message('what the fuck'), '', routing_key='wtf1')

        self.assertIsInstance(self.amqp.drain(wait=10), MessageReceived)
