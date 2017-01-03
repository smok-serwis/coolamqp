# coding=UTF-8
from __future__ import absolute_import, division, print_function
from coolamqp.uplink import ListenerThread
import time
from coolamqp.connection import NodeDefinition
from coolamqp.uplink import Connection
import logging


NODE = NodeDefinition('127.0.0.1', 5672, 'user', 'user', heartbeat=5)
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    lt = ListenerThread()
    lt.start()

    con = Connection(NODE, lt)

    con.start()

    time.sleep(50)

    lt.terminate()
