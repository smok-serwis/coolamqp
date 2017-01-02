# coding=UTF-8
from __future__ import absolute_import, division, print_function
from coolamqp.uplink import ListenerThread
import time
from coolamqp.connection.state import Broker
from coolamqp.connection import NodeDefinition



NODE = NodeDefinition('127.0.0.1', 5672, 'user', 'user', heartbeat=5)


if __name__ == '__main__':
    lt = ListenerThread()
    lt.start()

    broker = Broker.from_node_def(NODE, lt)

    broker.connect().wait()

    time.sleep(50)

    lt.terminate()
