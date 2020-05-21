# coding=UTF-8
from __future__ import absolute_import, division, print_function

"""
Provides reactors that can authenticate an AQMP session
"""
import six
import typing as tp
import copy
import logging
from coolamqp.framing.definitions import ConnectionStart, ConnectionStartOk, \
    ConnectionTune, ConnectionTuneOk, ConnectionOpen, ConnectionOpenOk
from coolamqp.framing.frames import AMQPMethodFrame
from coolamqp.uplink.connection.states import ST_ONLINE
from coolamqp.uplink.heartbeat import Heartbeater
from coolamqp import __version__

PUBLISHER_CONFIRMS = b'publisher_confirms'
CONSUMER_CANCEL_NOTIFY = b'consumer_cancel_notify'
CONNECTION_BLOCKED = b'connection.blocked'

SUPPORTED_EXTENSIONS = [
    PUBLISHER_CONFIRMS,
    CONSUMER_CANCEL_NOTIFY,     # half assed support - we just .cancel the consumer, see #12
    CONNECTION_BLOCKED
]

CLIENT_DATA = [
    # because RabbitMQ is some kind of a fascist and does not allow
    # these fields to be of type short-string
    (b'product', (b'CoolAMQP', 'S')),
    (b'version', (__version__.encode('utf8'), 'S')),
    (b'copyright', (b'Copyright (C) 2016-2020 SMOK sp. z o.o.', 'S')),
    (
        b'information', (
            b'Licensed under the MIT License.\nSee https://github.com/smok-serwis/coolamqp for details',
            'S')),
    (b'capabilities',
     ([(capa, (True, 't')) for capa in SUPPORTED_EXTENSIONS], 'F')),
]

WATCHDOG_TIMEOUT = 10

logger = logging.getLogger(__name__)


class Handshaker(object):
    """
    Object that given a connection rolls the handshake.
    """

    def __init__(self, connection,  # type: coolamqp.uplink.connection.Connection
                 node_definition,  # type: coolamqp.objects.NodeDefinition
                 on_success,  # type: tp.Callable[[], None]
                 extra_properties=None  # type: tp.Dict[bytes, tp.Tuple[tp.Any, str]]
                 ):
        """
        :param connection: Connection instance to use
        :type node_definition: NodeDefinition
        :param on_success: callable/0, on success
        """
        self.connection = connection
        self.login = node_definition.user.encode('utf8')
        self.password = node_definition.password.encode('utf8')
        self.virtual_host = node_definition.virtual_host.encode('utf8')
        self.heartbeat = node_definition.heartbeat or 0
        self.connection.watch_for_method(0, ConnectionStart,
                                         self.on_connection_start)

        # Callbacks
        self.on_success = on_success
        self.EXTRA_PROPERTIES = extra_properties or []

    # Called by internal setup
    def on_watchdog(self):
        """
        Called WATCHDOG_TIMEOUT seconds after setup begins

        If we are not ST_ONLINE after that much, something is wrong and pwn this connection.
        """
        # Not connected in 20 seconds - abort
        if self.connection.state != ST_ONLINE:
            # closing the connection this way will get to Connection by channels of ListenerThread
            self.connection.send(None)

    def on_connection_start(self, payload  # type: coolamqp.framing.base.AMQPPayload
                            ):

        sasl_mechanisms = payload.mechanisms.tobytes().split(b' ')
        locale_supported = payload.locales.tobytes().split(b' ')

        # Select a mechanism
        if b'PLAIN' not in sasl_mechanisms:
            raise ValueError('Server does not support PLAIN')

        # Select capabilities
        server_props = dict(payload.server_properties)
        if b'capabilities' in server_props:
            for label, fv in server_props[b'capabilities'][0]:
                if label in SUPPORTED_EXTENSIONS:
                    if fv[0]:
                        self.connection.extensions.append(label)

        self.connection.watchdog(WATCHDOG_TIMEOUT, self.on_watchdog)
        self.connection.watch_for_method(0, ConnectionTune,
                                         self.on_connection_tune)

        CLIENT_DATA_c = copy.copy(CLIENT_DATA)
        CLIENT_DATA_c.extend(self.EXTRA_PROPERTIES)
        self.connection.send([
            AMQPMethodFrame(0,
                            ConnectionStartOk(CLIENT_DATA_c, b'PLAIN',
                                              b'\x00' + self.login + b'\x00' + self.password,
                                              locale_supported[0]
                                              ))
        ])

    def on_connection_tune(self, payload  # type: coolamqp.framing.base.AMQPPayload
                           ):
        self.connection.frame_max = payload.frame_max
        self.connection.heartbeat = min(payload.heartbeat, self.heartbeat)
        self.connection.free_channels.extend(six.moves.xrange(1, (
            65535 if payload.channel_max == 0 else payload.channel_max) + 1))

        self.connection.watch_for_method(0, ConnectionOpenOk,
                                         self.on_connection_open_ok)
        self.connection.send([
            AMQPMethodFrame(0, ConnectionTuneOk(payload.channel_max,
                                                payload.frame_max,
                                                self.connection.heartbeat)),
            AMQPMethodFrame(0, ConnectionOpen(self.virtual_host))
        ])

        # Install heartbeat handlers NOW, if necessary
        if self.connection.heartbeat > 0:
            Heartbeater(self.connection, self.connection.heartbeat)

    def on_connection_open_ok(self, payload  # type: coolamqp.framing.base.AMQPPayload
                              ):
        self.on_success()
