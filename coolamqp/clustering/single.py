# coding=UTF-8
from __future__ import print_function, absolute_import, division

import logging
import typing as tp

try:
    from coolamqp.framing.definitions import ConnectionUnblocked, ConnectionBlocked
except ImportError:
    ConnectionBlocked, ConnectionUnblocked = None, None

from coolamqp.objects import Callable
from coolamqp.uplink import Connection
from coolamqp.uplink.connection import MethodWatch

logger = logging.getLogger(__name__)


class SingleNodeReconnector(object):
    """
    Connection to one node. It will do it's best to remain alive.
    """

    def __init__(self, node_def,  # type: coolamqp.objects.NodeDefinition
                 attache_group,  # type: coolamqp.attaches.AttacheGroup
                 listener_thread,  # type: coolamqp.uplink.ListenerThread
                 extra_properties=None,  # type: tp.Dict[bytes, tp.Tuple[tp.Any, str]]
                 log_frames=None,  # type: tp.Callable[]
                 name=None):
        self.listener_thread = listener_thread
        self.node_def = node_def
        self.attache_group = attache_group
        self.connection = None
        self.extra_properties = extra_properties
        self.log_frames = log_frames
        self.name = name or 'CoolAMQP'

        self.terminating = False
        self.timeout = None

        self.on_fail = Callable()  #: public
        self.on_blocked = Callable()  #: public
        self.on_fail.add(self._on_fail)

    def is_connected(self):  # type: () -> bool
        return self.connection is not None

    def connect(self, timeout=None):  # type: (tp.Optional[float]) -> None
        assert self.connection is None

        timeout = timeout or self.timeout
        self.timeout = timeout

        # Initiate connecting - this order is very important!
        self.connection = Connection(self.node_def, self.listener_thread,
                                     extra_properties=self.extra_properties,
                                     log_frames=self.log_frames,
                                     name=self.name)
        self.attache_group.attach(self.connection)
        self.connection.start(timeout)
        self.connection.finalize.add(self.on_fail)

        # Register the on-blocking watches
        if ConnectionBlocked is not None:
            mw = MethodWatch(0, (ConnectionBlocked,), lambda: self.on_blocked(True))
            mw.oneshot = False
            self.connection.watch(mw)

        if ConnectionUnblocked is not None:
            mw = MethodWatch(0, (ConnectionUnblocked,), lambda: self.on_blocked(False))
            mw.oneshot = False
            self.connection.watch(mw)

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
