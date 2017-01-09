# coding=UTF-8
from __future__ import absolute_import, division, print_function
from coolamqp.uplink import ListenerThread
import time, logging, threading
from coolamqp.objects import Message, MessageProperties
from coolamqp.connection import NodeDefinition
from coolamqp.uplink import Connection

from coolamqp.attaches import Consumer, Publisher, MODE_NOACK, MODE_CNPUB
from coolamqp.objects import Queue
import time


NODE = NodeDefinition('127.0.0.1', 'user', 'user', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    lt = ListenerThread()
    lt.start()

    con = Connection(NODE, lt)
    con.start()

    cons = Consumer(Queue('siema-eniu'), no_ack=True)
    cons.attach(con)


    class IPublishThread(threading.Thread):
        def __init__(self):
            super(IPublishThread, self).__init__()
            self.daemon = True

        def run(self):
            pub2 = Publisher(MODE_NOACK)
            pub2.attach(con)
            while True:
                pub2.publish(Message(b'you dawg'), routing_key=b'siema-eniu')


    IPublishThread().start()

    while True:
        time.sleep(10)

    lt.terminate()
