# coding=UTF-8
from __future__ import absolute_import, division, print_function

import unittest
import os
import time
from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, \
    ConnectionDown, ConsumerCancelled, Message, Exchange


NODE = ClusterNode('127.0.0.1', 'guest', 'guest')

from tests.utils import CoolAMQPTestCase


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


class TestFailures(CoolAMQPTestCase):

    def test_cancel_not_consumed_queue(self):
        self.amqp.cancel(Queue('hello world')).result()

    def test_longer_disconnects(self):
        os.system("sudo service rabbitmq-server stop")
        self.drainTo(ConnectionDown, 4)
        time.sleep(12)
        os.system("sudo service rabbitmq-server start")
        self.drainTo(ConnectionUp, 35)

    def test_qos_redeclared_on_fail(self):
        self.amqp.qos(0, 1).result()

        self.restart_rmq()

        self.amqp.consume(Queue('lol', exclusive=True)).result()
        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')

        p = self.drainTo(MessageReceived, 4)

        self.drainToNone(5)
        p.message.ack()
        self.assertIsInstance(self.amqp.drain(wait=4), MessageReceived)

    def test_connection_flags_are_okay(self):
        os.system("sudo service rabbitmq-server stop")
        self.assertIsInstance(self.amqp.drain(wait=4), ConnectionDown)
        self.assertFalse(self.amqp.connected)
        os.system("sudo service rabbitmq-server start")
        self.assertIsInstance(self.amqp.drain(wait=20), ConnectionUp)
        self.assertTrue(self.amqp.connected)

    def test_sending_a_message_is_cancelled(self):
        """are messages generated at all? does it reconnect?"""

        self.amqp.consume(Queue('wtf1', exclusive=True))

        os.system("sudo service rabbitmq-server stop")
        self.drainTo(ConnectionDown, 5)

        p = self.amqp.send(Message(b'what the fuck'), routing_key='wtf1')
        p.cancel()
        self.assertTrue(p.wait())
        self.assertFalse(p.has_failed())

        os.system("sudo service rabbitmq-server start")
        self.drainToAny([ConnectionUp], 30, forbidden=[MessageReceived])

    def test_qos_after_failure(self):
        self.amqp.qos(0, 1)

        self.amqp.consume(Queue('lol', exclusive=True)).result()
        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')

        p = self.amqp.drain(wait=4)
        self.assertIsInstance(p, MessageReceived)

        self.assertIsNone(self.amqp.drain(wait=5))
        p.message.ack()
        self.assertIsInstance(self.amqp.drain(wait=4), MessageReceived)

        self.restart_rmq()

        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')

        p = self.drainTo(MessageReceived, 4)

        self.drainToNone(5)
        p.message.ack()
        self.drainTo(MessageReceived, 4)

    def test_connection_down_and_up_redeclare_queues(self):
        """are messages generated at all? does it reconnect?"""

        q1 = Queue('wtf1', exclusive=True)
        self.amqp.consume(q1).result()

        self.restart_rmq()

        self.amqp.send(Message(b'what the fuck'), routing_key='wtf1')

        self.drainTo(MessageReceived, 20)

    def test_exchanges_are_redeclared(self):
        xchg = Exchange('a_fanout', type='fanout')
        self.amqp.declare_exchange(xchg)

        q1 = Queue('q1', exclusive=True, exchange=xchg)
        q2 = Queue('q2', exclusive=True, exchange=xchg)

        self.amqp.consume(q1)
        self.amqp.consume(q2).result()

        self.restart_rmq()

        self.amqp.send(Message(b'hello'), xchg)
        self.drainTo([MessageReceived, MessageReceived], 20)

    def test_consuming_exclusive_queue(self):
        # declare and eat
        q1 = Queue('q1', exclusive=True)

        self.amqp.consume(q1).wait()

        with self.new_amqp_connection() as amqp2:
            q2 = Queue('q1', exclusive=True)

            r = amqp2.consume(q2)
            self.assertFalse(r.wait())
