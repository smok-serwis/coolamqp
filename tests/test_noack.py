# coding=UTF-8
from __future__ import absolute_import, division, print_function
import six
import os
import time

from tests.utils import CoolAMQPTestCase
from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, ConnectionDown, ConsumerCancelled, Message, Exchange

class TestNoAcknowledge(CoolAMQPTestCase):
    def test_noack_works(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.qos(0, 1, False)

        self.amqp.consume(myq, no_ack=True)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.drainTo([MessageReceived, MessageReceived, MessageReceived], [3, 3, 3])

    def test_noack_works_after_restart(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.qos(0, 1, False)

        self.amqp.consume(myq, no_ack=True)

        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.drainTo([MessageReceived, MessageReceived, MessageReceived], [3, 3, 3])

        self.restart_rmq()

        self.amqp.send(Message(b'what the fuck'), routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), routing_key='myqueue')
        self.amqp.send(Message(b'what the fuck'), routing_key='myqueue')

        self.drainTo([MessageReceived, MessageReceived, MessageReceived], [3, 3, 3])

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
        self.drainTo(MessageReceived, 1).message.ack() # 2nd
        self.drainTo(MessageReceived, 1).message.ack() # 3rd

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