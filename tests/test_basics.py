# coding=UTF-8
from __future__ import absolute_import, division, print_function
import six

from coolamqp import Cluster, ClusterNode, Queue, MessageReceived, ConnectionUp, ConsumerCancelled, Message, Exchange

from tests.utils import getamqp, CoolAMQPTestCase

class TestThings(CoolAMQPTestCase):
    INIT_AMQP = False

    def test_different_constructor_for_clusternode(self):
        cn = ClusterNode(host='127.0.0.1', user='guest', password='guest', virtual_host='/')
        amqp = Cluster([cn])
        amqp.start()
        self.assertIsInstance(amqp.drain(1), ConnectionUp)
        amqp.shutdown()


class TestBasics(CoolAMQPTestCase):

    def test_acknowledge(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        p = self.drainTo(MessageReceived, 4)
        self.assertEquals(p.message.body, b'what the fuck')
        self.assertIsInstance(p.message.body, six.binary_type)
        p.message.ack()

        self.assertIs(self.amqp.drain(wait=1), None)

    def test_send_bullshit(self):
        self.assertRaises(TypeError, lambda: Message(u'what the fuck'))

    def test_send_nonobvious_bullshit(self):
        self.assertEquals(Message(bytearray(b'what the fuck')).body, b'what the fuck')

    def test_nacknowledge(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        p = self.drainTo(MessageReceived, 4)
        self.assertEquals(p.message.body, b'what the fuck')
        p.message.nack()

        p = self.drainTo(MessageReceived, 4)
        self.assertEquals(p.message.body, b'what the fuck')

    def test_bug_hangs(self):
        p = Queue('lol', exclusive=True)
        self.amqp.consume(p)
        self.amqp.consume(p).result()

    def test_consume_declare(self):
        """Spawn a second connection. One declares an exclusive queue, other tries to consume from it"""
        with self.new_amqp_connection() as amqp2:

            has_failed = {'has_failed': False}

            self.amqp.declare_queue(Queue('lol', exclusive=True)).result()
            amqp2.consume(Queue('lol', exclusive=True), on_failed=lambda e: has_failed.update({'has_failed': True})).result()

            self.assertTrue(has_failed['has_failed'])

    def test_qos(self):
        self.amqp.qos(0, 1)

        self.amqp.consume(Queue('lol', exclusive=True)).result()
        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')
        self.amqp.send(Message(b'what the fuck'), '', routing_key='lol')

        p = self.drainTo(MessageReceived, 4)

        self.drainToNone(5)
        p.message.ack()
        self.assertIsInstance(self.amqp.drain(wait=4), MessageReceived)

    def test_consume_twice(self):
        """Spawn a second connection and try to consume an exclusive queue twice"""
        with self.new_amqp_connection() as amqp2:

            has_failed = {'has_failed': False}

            self.amqp.consume(Queue('lol', exclusive=True)).result()
            amqp2.consume(Queue('lol', exclusive=True), on_failed=lambda e: has_failed.update({'has_failed': True})).result()

            self.assertTrue(has_failed['has_failed'])

    def test_send_and_receive(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.send(Message(b'what the fuck'), '', routing_key='myqueue')

        self.assertEquals(self.drainTo(MessageReceived, 3).message.body, b'what the fuck')

    def test_consumer_cancelled_on_queue_deletion(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.delete_queue(myq)

        self.assertEquals(self.drainTo(ConsumerCancelled, 5).reason, ConsumerCancelled.BROKER_CANCEL)

    def test_consumer_cancelled_on_consumer_cancel(self):
        myq = Queue('myqueue', exclusive=True)

        self.amqp.consume(myq)
        self.amqp.cancel(myq)

        c = self.drainTo(ConsumerCancelled, 10)
        self.assertEquals(c.reason, ConsumerCancelled.USER_CANCEL)

    def test_delete_exchange(self):
        xchg = Exchange('a_fanout', type='fanout')
        self.amqp.declare_exchange(xchg)
        self.amqp.delete_exchange(xchg).result()

    def test_exchanges(self):
        xchg = Exchange('a_fanout', type='fanout')
        self.amqp.declare_exchange(xchg)

        q1 = Queue('q1', exclusive=True, exchange=xchg)
        q2 = Queue('q2', exclusive=True, exchange=xchg)

        self.amqp.consume(q1)
        self.amqp.consume(q2)

        self.amqp.send(Message(b'hello'), xchg)

        self.drainTo(MessageReceived, 4)
        self.drainTo(MessageReceived, 4)
