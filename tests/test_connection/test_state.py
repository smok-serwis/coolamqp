# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest


from coolamqp.connection.state import Broker
from coolamqp.connection import NodeDefinition
from coolamqp.uplink import ListenerThread, Connection, Handshaker
import socket
import time


def newc():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5672))
    s.settimeout(0)
    s.send('AMQP\x00\x00\x09\x01')
    return s


NODE = NodeDefinition('127.0.0.1', 5672, 'user', 'user')


class TestState(unittest.TestCase):
    def test_basic(self):
        lt = ListenerThread()
        lt.start()

        broker = Broker(Connection(newc(), lt), NODE)

        ord = broker.connect()
        ord.wait()

        time.sleep(100)

        lt.terminate()
