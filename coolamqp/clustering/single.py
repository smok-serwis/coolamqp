# coding=UTF-8
from __future__ import print_function, absolute_import, division
import six
import random
import logging
import itertools

from coolamqp.uplink import Connection
from coolamqp.objects import Callable

logger = logging.getLogger(__name__)


class SingleNodeReconnector(object):
    """
    Connection to one node at a time. It will do it's best to remain alive.
    It will try to connect to each specified node, in such order.
    """

    def __init__(self, node_def, attache_group, listener_thread):
        self.listener_thread = listener_thread

        from coolamqp.objects import NodeDefinition
        if isinstance(node_def, NodeDefinition):
            node_def = [node_def]
        self.nodes = itertools.cycle(node_def)

        self.node_def = six.next(self.nodes)
        self.attache_group = attache_group
        self.connection = None

        self.terminating = False

        self.on_fail = Callable()  #: public

        self.on_fail.add(self._on_fail)

    def is_connected(self):
        return self.connection is not None

    def connect(self):
        assert self.connection is None

        # Initiate connecting - this order is very important!
        self.node_def = six.next(self.nodes)
        self.connection = Connection(self.node_def, self.listener_thread)
        self.attache_group.attach(self.connection)
        self.connection.start()
        self.connection.finalize.add(self.on_fail)

    def _on_fail(self):
        if self.terminating:
            return

        self.connection = None
        self.listener_thread.call_next_io_event(self.connect)

    def shutdown(self):
        """Close this connection"""
        self.terminating = True

        if self.connection is not None:
            self.connection.send(None)
            self.connection = None
