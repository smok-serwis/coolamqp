# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
import six
import os
import time

from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, ConnectionDown, ConsumerCancelled, Message, Exchange

class TestNoAcknowledge(unittest.TestCase):

    def drainTo(self, type_, timeout=20):
        start = time.time()
        while time.time() - start < timeout:
            q = self.amqp.drain(1)
            if isinstance(q, type_):
                return q
        self.fail('Did not find %s' % (type_, ))

    def setUp(self):
        self.amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
        self.amqp.start()
        self.drainTo(ConnectionUp, timeout=1)

    def tearDown(self):
        self.amqp.shutdown()

    def test_noack_works(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.qos(0, 1, False)

        self.amqp.consume(myq, no_ack=True)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.drainTo(MessageReceived)
        self.drainTo(MessageReceived)
        self.drainTo(MessageReceived)

    def test_noack_works_after_restart(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.qos(0, 1, False)

        self.amqp.consume(myq, no_ack=True)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.assertIsInstance(self.amqp.drain(wait=1), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)

        os.system("sudo service rabbitmq-server restart")
        self.assertIsInstance(self.amqp.drain(wait=5), ConnectionDown)
        self.assertIsInstance(self.amqp.drain(wait=5), ConnectionUp)

        self.amqp.send(Message(b'what the fuck'), routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), routing_key='myqueue')

        self.assertIsInstance(self.amqp.drain(wait=1), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)
        self.assertIsInstance(self.amqp.drain(wait=0.3), MessageReceived)

    def test_noack_coexists(self):
        self.amqp.qos(0, 1, False)

        self.amqp.consume(Queue('myqueue', exclusive=True), no_ack=True)
        self.amqp.consume(Queue('myqueue2', exclusive=True))

        msg = Message(b'zz')

        for i in range(3):
            self.amqp.send(msg, routing_key='myqueue')
            self.amqp.send(msg, routing_key='myqueue2')

        mq2s = []
        for i in range(4):
            # I should have received 3 messages from myqueue, and 2 from myqueue2
            print('beng')
            mer = self.drainTo(MessageReceived)
            if mer.message.routing_key == 'myqueue2':
                mq2s.append(mer.message)

        # Should receive nothing, since not acked
        self.assertIsNone(self.amqp.drain(wait=4))

        self.assertEquals(len(mq2s), 1)

        # ack and receive
        for me in mq2s: me.ack()
        mer = self.amqp.drain(wait=1)       # 2nd
        self.assertIsInstance(mer, MessageReceived)
        mer.message.ack()
        mer = self.amqp.drain(wait=1)       # 3rd
        self.assertIsInstance(mer, MessageReceived)
        mer.message.ack()

    @unittest.skip('demonstrates a py-amqp bug')
    def test_noack_coexists_empty_message_body(self):
        self.amqp.qos(0, 1, False)

        self.amqp.consume(Queue('myqueue', exclusive=True), no_ack=True)
        self.amqp.consume(Queue('myqueue2', exclusive=True))

        msg = Message(b'')      # if this is empty, py-amqp fails

        for i in range(3):
            self.amqp.send(msg, routing_key='myqueue')
            self.amqp.send(msg, routing_key='myqueue2')

        # And here connection with the broker snaps .....

        mq2s = []
        for i in range(4):
            # I should have received 3 messages from myqueue, and 2 from myqueue2
            mer = self.drainTo(MessageReceived)
            if mer.message.routing_key == 'myqueue2':
                mq2s.append(mer.message)

        # Should receive nothing, since not acked
        self.assertIsNone(self.amqp.drain(wait=4))

        self.assertEquals(len(mq2s), 1)

        # ack and receive
        for me in mq2s: me.ack()
        mer = self.amqp.drain(wait=1)       # 2nd
        self.assertIsInstance(mer, MessageReceived)
        mer.message.ack()
        mer = self.amqp.drain(wait=1)       # 3rd
        self.assertIsInstance(mer, MessageReceived)
        mer.message.ack()