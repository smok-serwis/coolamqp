# coding=UTF-8
from __future__ import print_function, absolute_import, division
import six
import logging

from coolamqp.uplink import Connection
from coolamqp.objects import Callable

logger = logging.getLogger(__name__)


class SingleNodeReconnector(object):
    """
    Connection to one node. It will do it's best to remain alive.
    """

    def __init__(self, node_def, attache_group, listener_thread):
        self.listener_thread = listener_thread
        self.node_def = node_def
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
        self.connection = Connection(self.node_def, self.listener_thread)
        self.attache_group.attach(self.connection)
        self.connection.start()
        self.connection.finalize.add(self.on_fail)

    def _on_fail(self):
        if self.terminating:
            return

        self.connection = None
        self.call_next_io_event(self.connect)

    def shutdown(self):
        """Close this connection"""
        self.terminating = True

        if self.connection is not None:
            self.connection.send(None)
            self.connection = None
