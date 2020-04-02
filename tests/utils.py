# coding=UTF-8
from __future__ import absolute_import, division, print_function

import collections
import os
import socket
import time
import unittest

import monotonic
from coolamqp.backends.base import AMQPBackend, ConnectionFailedError

from coolamqp import Cluster, ClusterNode, ConnectionDown, \
    ConnectionUp, ConsumerCancelled


def getamqp():
    amqp = Cluster([ClusterNode(os.environ.get('AMQP_HOST', '127.0.0.1'), 'guest', 'guest')], extra_properties=[
        (b'mode', (b'Testing', 'S')),
    ])
    amqp.start()
    return amqp


class CoolAMQPTestCase(unittest.TestCase):
    """
    Base class for all CoolAMQP tests. Creates na AMQP connection, provides methods
    for easy interfacing, and other utils.
    """
    INIT_AMQP = True  # override on child classes

    def setUp(self):
        if self.INIT_AMQP:
            self.__newam = self.new_amqp_connection()
            self.amqp = self.__newam.__enter__()

    def tearDown(self):
        # if you didn't unfail AMQP, that means you don't know what you doing
        self.assertRaises(AttributeError, lambda: self.old_backend)

        if self.INIT_AMQP:
            self.__newam.__exit__(None, None, None)

    def drainToNone(self, timeout=4):
        self.assertIsNone(self.amqp.drain(4))

    def drainToAny(self, types, timeout, forbidden=[]):
        """Assert that messages with types, in any order, are found within timeout.
        Fail if any type from forbidden is found"""
        start = monotonic.monotonic()
        types = set(types)
        while monotonic.monotonic() - start < timeout:
            q = self.amqp.drain(1)
            if type(q) in forbidden:
                self.fail('%s found', type(q))
            if type(q) in types:
                types.remove(type(q))
        if len(types) > 0:
            self.fail('Not found %s' % (''.join(map(str, types)),))

    def drainTo(self, type_, timeout, forbidden=[ConsumerCancelled]):
        """
        Return next event of type_. It has to occur within timeout, or fail.

        If you pass iterable (len(type_) == len(timeout), last result will be returned
        and I will drainTo() in order.
        """
        if isinstance(type_, collections.Iterable):
            self.assertIsInstance(timeout, collections.Iterable)
            for tp, ti in zip(type_, timeout):
                p = self.drainTo(tp, ti)
                if type(p) in forbidden:
                    self.fail('Found %s but forbidden', type(p))
            return p

        start = monotonic.monotonic()
        while monotonic.monotonic() - start < timeout:
            q = self.amqp.drain(1)
            if isinstance(q, type_):
                return q
        self.fail('Did not find %s' % (type_,))

    def takes_less_than(self, max_time):
        """
        Tests that your code executes in less time than specified value.
        Use like:

            with self.takes_less_than(0.9):
                my_operation()

        :param max_time: in seconds
        """
        return TakesLessThanCM(self, max_time)

    # ======failures
    def single_fail_amqp(self):  # insert single failure
        sock = self.amqp.thread.backend.channel.connection.transport.sock
        self.amqp.thread.backend.channel.connection.transport.sock = FailbowlSocket()
        self.amqp.thread.backend.channel.connection = None  # 'connection already closed' or sth like that

        sock.close()

    def fail_amqp(self):  # BROKER DEAD: SWITCH ON

        self.old_backend = self.amqp.backend
        self.amqp.backend = FailbowlBackend

    def unfail_amqp(self):  # BROKER DEAD: SWITCH OFF
        self.amqp.backend = self.old_backend
        del self.old_backend

    def restart_rmq(self):  # simulate a broker restart
        self.fail_amqp()
        self.single_fail_amqp()
        time.sleep(3)
        self.unfail_amqp()

        self.drainTo([ConnectionDown, ConnectionUp], [5, 20])

    def new_amqp_connection(self, consume_connectionup=True):
        return AMQPConnectionCM(self, consume_connectionup=consume_connectionup)


class TakesLessThanCM(object):
    def __init__(self, testCase, max_time):
        self.test = testCase
        self.max_time = max_time

    def __enter__(self, testCase, max_time):
        self.started_at = time.time()
        return lambda: time.time() - self.started_at > self.max_time  # is_late

    def __exit__(self, tp, v, tb):
        self.test.assertLess(time.time() - self.started_at, self.max_time)
        return False


class AMQPConnectionCM(object):
    """Context manager. Get new AMQP uplink. Consume ConnectionUp if consume_connectionup

    Use like:

        with self.new_amqp_connection() as amqp2:
            amqp2.consume(...)

    """

    def __init__(self, testCase, consume_connectionup):
        self.test = testCase
        self.consume_connectionup = consume_connectionup

    def __enter__(self):
        self.amqp = getamqp()
        if self.consume_connectionup:
            self.test.assertIsInstance(self.amqp.drain(3), ConnectionUp)
        return self.amqp

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.amqp.shutdown()
        return False


class FailbowlBackend(AMQPBackend):
    def __init__(self, node, thread):
        AMQPBackend.__init__(self, node, thread)
        raise ConnectionFailedError('Failbowl')


class FailbowlSocket(object):
    def __getattr__(self, item):
        def failbowl(*args, **kwargs):
            time.sleep(1)  # hang and fail
            raise socket.error

        def sleeper(*args, **kwargs):
            time.sleep(1)  # hang and fail

        if item in ('close', 'shutdown'):
            return sleeper
        else:
            return failbowl
