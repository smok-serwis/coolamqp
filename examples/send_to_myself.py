from coolamqp import Cluster, ClusterNode, Queue, Message, ConnectionUp, ConnectionDown, MessageReceived, ConsumerCancelled
import logging
import time

QUEUE_NAME = 'f'

logging.basicConfig()

cluster = Cluster([ClusterNode('xx', 'xx', 'xx', 'xx', heartbeat=10)]).start()

a_queue = Queue(QUEUE_NAME, auto_delete=True)
cluster.consume(a_queue)

q = time.time()
while True:
    if time.time() - q > 10:
        q = time.time()
        cluster.send(Message('hello world'), routing_key=QUEUE_NAME)

    evt = cluster.drain(2)

    if isinstance(evt, ConnectionUp):
        print 'Connection is up'
    elif isinstance(evt, ConnectionDown):
        print 'Connection is down'
    elif isinstance(evt, MessageReceived):
        print 'Message is %s' % (evt.message.body, )
        evt.message.ack()
    elif isinstance(evt, ConsumerCancelled):
        print 'Consumer %s cancelled' % (evt.queue.name, )


