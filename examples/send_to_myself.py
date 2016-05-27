from coolamqp import Cluster, ClusterNode, Queue, Message, ConnectionUp, ConnectionDown, MessageReceived
import logging
import time

QUEUE_NAME = 'f'

logging.basicConfig()

cluster = Cluster([ClusterNode('xx', 'xx', 'xx', 'xx', heartbeat=10)]).start()

a_queue = Queue(QUEUE_NAME, auto_delete=True)
cluster.consume(a_queue)

q = time.time()
i = 0

while True:
    if time.time() - q > 10:
        q = time.time()
        cluster.send(Message('hello world '+str(i)), routing_key=QUEUE_NAME)
        i += 1

    evt = cluster.drain(2)

    if isinstance(evt, ConnectionUp):
        print 'Connection is up'
    elif isinstance(evt, ConnectionDown):
        print 'Connection is down'
    elif isinstance(evt, MessageReceived):
        print 'Message is %s' % (evt.message.body, )
        evt.message.ack()


