# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
import six
import time

from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, \
    ConnectionDown, ConsumerCancelled, Message, Exchange


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
        self.amqp.start()
        self.assertIsInstance(self.amqp.drain(1), ConnectionUp)

    def tearDown(self):
        self.amqp.shutdown()

    def takes_less_than(self, max_time):
        """
        Tests that your code executes in less time than specified value.
        Use like:

            with self.takes_less_than(0.9):
                my_operation()

        :param max_time: in seconds
        """
        test = self

        class CM(object):
            def __enter__(self):
                self.started_at = time.time()

            def __exit__(self, tp, v, tb):
                test.assertLess(time.time() - self.started_at, max_time)
                return False

        return CM()

    def test_sending_a_message(self):

        with self.takes_less_than(0.5):
            self.amqp.send(Message(b''), routing_key='nowhere').result()

