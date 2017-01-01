# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest

from coolamqp.handshake import Handshaker
from coolamqp.uplink import ListenerThread, Connection
import socket
import time


def newc():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5672))
    s.settimeout(0)
    s.send('AMQP\x00\x00\x09\x01')
    return s


class TestBasic(unittest.TestCase):
    def test_gets_connectionstart(self):

        hnd_ok = {'ok': False}
        def hnd_suc():
            hnd_ok['ok'] = True

        lt = ListenerThread()
        lt.start()

        con = Connection(newc(), lt)

        Handshaker(con, 'user', 'user', '/', hnd_suc, lambda: None)
        con.start()

        time.sleep(5)

        lt.terminate()
        self.assertTrue(hnd_ok['ok'])
