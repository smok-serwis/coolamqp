# coding=UTF-8

from __future__ import print_function, absolute_import, division
import six
import unittest
import time, logging, threading, monotonic
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, ReceivedMessage, Exchange
from coolamqp.clustering import Cluster, MessageReceived, NothingMuch

import time
NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


class TestConnecting(unittest.TestCase):

    def test_start_called_multiple_times(self):
        c = Cluster([NODE])
        c.start(wait=True)
        self.assertRaises(RuntimeError, lambda: c.start())
        c.shutdown(wait=True)

    def test_shutdown_without_start(self):
        c = Cluster([NODE])
        self.assertRaises(RuntimeError, lambda: c.shutdown())
