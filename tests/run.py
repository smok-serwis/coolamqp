# coding=UTF-8
from __future__ import absolute_import, division, print_function
from coolamqp.uplink import ListenerThread
import time
from coolamqp.connection import NodeDefinition
from coolamqp.uplink import Connection
import logging

from coolamqp.attaches import Consumer
from coolamqp.messages import Queue


NODE = NodeDefinition('127.0.0.1', 5672, 'user', 'user', heartbeat=5)
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    lt = ListenerThread()
    lt.start()

    con = Connection(NODE, lt)
    con.start()

    cons = Consumer(Queue('siema-eniu'), no_ack=False)
    cons.attach(con)

    while True:
        time.sleep(10)

    lt.terminate()
