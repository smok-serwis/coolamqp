# coding=UTF-8
"""
This is the layer that makes your consumers and publishers survive connection losses.
It also renegotiates connections, shall they fail, and implements some sort of exponential delay policy.

EVERYTHING HERE IS CALLED BY LISTENER THREAD UNLESS STATED OTHERWISE.

"""
from __future__ import print_function, absolute_import, division
import six
import logging

from coolamqp.uplink import FailWatch, Connection

logger = logging.getLogger(__name__)



class SingleNodeReconnector(object):
    """
    This has a Listener Thread, a Node Definition, and an attache group,
    and tries to keep all the things relatively alive.
    """

    def __init__(self, node_def, attache_group, listener_thread):
        self.listener_thread = listener_thread
        self.node_def = node_def
        self.attache_group = attache_group
        self.connection = None

    def connect(self):
        assert self.connection is None

        # Initiate connecting
        self.connection = Connection(self.node_def, self.listener_thread)
        self.connection.start()
        self.connection.watch(FailWatch(self.on_fail))
        self.attache_group.attach(self.connection)

    def on_fail(self):
        logger.info('Reconnecting...')
        self.connection = None
        self.connect()
