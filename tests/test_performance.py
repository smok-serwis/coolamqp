# coding=UTF-8
from __future__ import absolute_import, division, print_function
from tests.utils import CoolAMQPTestCase
import six
import time

from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, \
    ConnectionDown, ConsumerCancelled, Message, Exchange


class TestBasics(CoolAMQPTestCase):
    def setUp(self):
        self.amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
        self.amqp.start()
        self.assertIsInstance(self.amqp.drain(1), ConnectionUp)

    def tearDown(self):
        self.amqp.shutdown()

    def test_sending_a_message(self):

        with self.takes_less_than(0.5):
            self.amqp.send(Message(b''), routing_key='nowhere').result()

