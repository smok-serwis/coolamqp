# coding=UTF-8
from __future__ import absolute_import, division, print_function
from coolamqp.uplink import ListenerThread
import time, logging, threading
from coolamqp.objects import Message, MessageProperties, NodeDefinition
from coolamqp.uplink import Connection

from coolamqp.attaches import Consumer, Publisher, AttacheGroup
from coolamqp.objects import Queue
from coolamqp.persistence import SingleNodeReconnector
import time


NODE = NodeDefinition('127.0.0.1', 'user', 'user', heartbeat=20)
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    lt = ListenerThread()
    lt.start()

    ag = AttacheGroup()
    snr = SingleNodeReconnector(NODE, ag, lt)
    snr.connect()

    ag.add(Consumer(Queue('siema-eniu'), no_ack=False, qos=(None, 20)))

    class IPublishThread(threading.Thread):
        def __init__(self, ag):
            super(IPublishThread, self).__init__()
            self.ag = ag
            self.daemon = True

        def run(self):
            pub2 = Publisher(Publisher.MODE_NOACK)
            self.ag.add(pub2)
            while True:
                pub2.publish(Message(b'you dawg', properties=MessageProperties(content_type='text/plain')),
                             routing_key=b'siema-eniu')
                time.sleep(0.1)

    IPublishThread(ag).start()

    while True:
        time.sleep(30)



    lt.terminate()
