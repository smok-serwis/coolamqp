# coding=UTF-8
from __future__ import absolute_import, division, print_function
import unittest
from threading import Lock
import time
import collections
import os
import monotonic

from coolamqp import Cluster, ClusterNode, ConnectionUp, ConnectionDown, ConnectionUp, ConsumerCancelled


def getamqp():
    amqp = Cluster([ClusterNode('127.0.0.1', 'guest', 'guest')])
    amqp.start()
    return amqp


class CoolAMQPTestCase(unittest.TestCase):
    """
    Base class for all CoolAMQP tests. Creates na AMQP connection, provides methods
    for easy interfacing, and other utils.
    """
    INIT_AMQP = True      # override on child classes


    def new_amqp_connection(self, consume_connectionup=True):
        obj = self

        class CM(object):
            """Context manager. Get new AMQP uplink. Consume ConnectionUp if consume_connectionup

            Use like:

                with self.new_amqp_connection() as amqp2:
                    amqp2.consume(...)

            """
            def __enter__(self):
                self.amqp = getamqp()
                if consume_connectionup:
                    obj.assertIsInstance(self.amqp.drain(3), ConnectionUp)
                return self.amqp

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.amqp.shutdown()
                return False
        return CM()
    def restart_rmq(self):
        # forcibly reset the connection
        class FailbowlSocket(object):
            def __getattr__(self, name):
                import socket
                raise socket.error()

        self.amqp.thread.backend.channel.connection.transport.sock = FailbowlSocket()

        self.drainTo([ConnectionDown, ConnectionUp], [5, 10])

    def setUp(self):
        if self.INIT_AMQP:
            os.system('sudo service rabbitmq-server start') # if someone killed it
            self.__newam = self.new_amqp_connection()
            self.amqp = self.__newam.__enter__()

    def tearDown(self):
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
            self.fail('Not found %s' % (''.join(map(str, types)), ))

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
        self.fail('Did not find %s' % (type_, ))

    def takes_less_than(self, max_time):
        """
        Tests that your code executes in less time than specified value.
        Use like:

            with self.takes_less_than(0.9):
                my_operation()

        :param max_time: in seconds
        """
        test = self

        class CM(object):
            def __enter__(self):
                self.started_at = time.time()

            def __exit__(self, tp, v, tb):
                test.assertLess(time.time() - self.started_at, max_time)
                return False

        return CM()
