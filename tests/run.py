# coding=UTF-8
from __future__ import absolute_import, division, print_function
from coolamqp.uplink import ListenerThread, Connection
import socket
import time
from coolamqp.connection.state import Broker
from coolamqp.connection import NodeDefinition

from coolamqp.uplink.transcript import SessionTranscript


def newc():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5672))
    s.settimeout(0)
    s.send('AMQP\x00\x00\x09\x01')
    return s


from coolamqp.uplink import Handshaker
NODE = NodeDefinition('127.0.0.1', 5672, 'user', 'user', heartbeat=5)



if __name__ == '__main__':
    lt = ListenerThread()
    lt.start()

    con = Connection(newc(), lt)
    con.transcript = SessionTranscript()
    broker = Broker(con, NODE)

    broker.connect()

    time.sleep(50)

    lt.terminate()
