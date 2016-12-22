#coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest


from coolamqp import Cluster, ClusterNode

class MyTestCase(unittest.TestCase):
    def test_connect(self):
        amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
        amqp.start()
        amqp.shutdown()

