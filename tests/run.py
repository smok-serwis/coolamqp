# coding=UTF-8
from __future__ import absolute_import, division, print_function
import time, logging, threading
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue
from coolamqp.clustering import Cluster

import time


NODE = NodeDefinition('127.0.0.1', 'user', 'user', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    amqp = Cluster([NODE])
    amqp.start(wait=True)


    c1 = amqp.consume(Queue(b'siema-eniu', exclusive=True), qos=(None, 20))
    c2 = amqp.consume(Queue(b'jo-malina', exclusive=True))

    while True:
        time.sleep(30)

    amqp.shutdown(True)
