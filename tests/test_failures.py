#coding=UTF-8
from __future__ import absolute_import, division, print_function

import unittest
import os
import time
from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, \
    ConnectionDown, ConsumerCancelled, Message, Exchange


NODE = ClusterNode('127.0.0.1', 'guest', 'guest')


class TestSpecialCases(unittest.TestCase):
    def test_termination_while_disconnect(self):
        self.amqp = Cluster([NODE])
        self.amqp.start()
        self.assertIsInstance(self.amqp.drain(wait=1), ConnectionUp)

        os.system("sudo service rabbitmq-server stop")
        time.sleep(5)
        self.assertIsInstance(self.amqp.drain(wait=1), ConnectionDown)

        self.amqp.shutdown()
        self.assertIsNone(self.amqp.thread.backend)
        self.assertFalse(self.amqp.connected)

        os.system("sudo service rabbitmq-server start")


class TestFailures(unittest.TestCase):

    def setUp(self):
        self.amqp = Cluster([NODE])
        self.amqp.start()
        self.assertIsInstance(self.amqp.drain(1), ConnectionUp)

    def tearDown(self):
        self.amqp.shutdown()

    def test_connection_down_and_up(self):
        """are messages generated at all? does it reconnect?"""
        os.system("sudo service rabbitmq-server restart")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=6), ConnectionUp)

    def test_longer_disconnects(self):
        os.system("sudo service rabbitmq-server stop")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        time.sleep(12)
        os.system("sudo service rabbitmq-server start")
        self.assertIsInstance(self.amqp.drain(wait=30), ConnectionUp)

    def test_qos_redeclared_on_fail(self):
        self.amqp.qos(0, 1).result()

        os.system("sudo service rabbitmq-server restart")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionUp)

        self.amqp.consume(Queue('lol', exclusive=True)).result()
        self.amqp.send(Message('what the fuck'), '', routing_key='lol')
        self.amqp.send(Message('what the fuck'), '', routing_key='lol')

        p = self.amqp.drain(wait=4)
        self.assertIsInstance(p, MessageReceived)

        self.assertIs(self.amqp.drain(wait=5), None)
        p.message.ack()
        self.assertIsInstance(self.amqp.drain(wait=4), MessageReceived)

    def test_connection_flags_are_okay(self):
        os.system("sudo service rabbitmq-server stop")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertFalse(self.amqp.connected)
        os.system("sudo service rabbitmq-server start")
        self.assertIsInstance(self.amqp.drain(wait=6), ConnectionUp)
        self.assertTrue(self.amqp.connected)


    def test_sending_a_message_is_cancelled(self):
        """are messages generated at all? does it reconnect?"""

        q1 = Queue('wtf1', exclusive=True)
        self.amqp.consume(q1).result()

        os.system("sudo service rabbitmq-server stop")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        result = self.amqp.send(Message('what the fuck'), '', routing_key='wtf1')
        result.cancel()

        os.system("sudo service rabbitmq-server start")

        self.assertIsInstance(self.amqp.drain(wait=6), ConnectionUp)
        self.assertIsNone(self.amqp.drain(wait=6))    # message is NOT received


    def test_connection_down_and_up_redeclare_queues(self):
        """are messages generated at all? does it reconnect?"""

        q1 = Queue('wtf1', exclusive=True)
        self.amqp.consume(q1).result()

        os.system("sudo service rabbitmq-server restart")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=6), ConnectionUp)

        self.amqp.send(Message('what the fuck'), '', routing_key='wtf1')

        self.assertIsInstance(self.amqp.drain(wait=10), MessageReceived)

    def test_exchanges_are_redeclared(self):
        xchg = Exchange('a_fanout', type='fanout')
        self.amqp.declare_exchange(xchg)

        q1 = Queue('q1', exclusive=True, exchange=xchg)
        q2 = Queue('q2', exclusive=True, exchange=xchg)

        self.amqp.consume(q1)
        self.amqp.consume(q2).result()

        os.system('sudo service rabbitmq-server restart')

        self.amqp.send(Message('hello'), xchg)
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionUp)
        self.assertIsInstance(self.amqp.drain(wait=4), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=4), MessageReceived)
