# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest

from coolamqp.framing.definitions import ConnectionStart
from coolamqp.uplink import ListenerThread, Connection, Reactor
import socket
import time


def newc():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5672))
    s.settimeout(0)
    s.send('AMQP\x00\x00\x09\x01')
    return s


class LolReactor(Reactor):
    def __init__(self):
        Reactor.__init__(self)
        self.got_connectionstart = False

    def on_frame(self, frame):
        if isinstance(frame.payload, ConnectionStart):
            self.got_connectionstart = True


class TestBasic(unittest.TestCase):
    def test_gets_connectionstart(self):
        lt = ListenerThread()
        lt.start()
        r = LolReactor()
        con = Connection(newc(), lt, r)

        time.sleep(5)

        lt.terminate()
        self.assertTrue(r.got_connectionstart)