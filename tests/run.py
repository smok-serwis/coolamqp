# coding=UTF-8
from __future__ import absolute_import, division, print_function
import time, logging, threading
from coolamqp.objects import Message, MessageProperties, NodeDefinition, Queue, Exchange
from coolamqp.exceptions import AMQPError
from coolamqp.clustering import Cluster

import time


NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    amqp = Cluster([NODE])
    amqp.start(wait=True)

    a = Exchange(u'jolax', type='fanout', auto_delete=True)
    bad = Exchange(u'jolax', type='direct', auto_delete=True)

    amqp.declare(a).result()

    try:
        amqp.declare(bad).result()
    except AMQPError:
        print(':)')

    while True:
        time.sleep(30)

    amqp.shutdown(True)
