# coding=UTF-8
from __future__ import absolute_import, division, print_function
"""
Provides reactors that can authenticate an AQMP session
"""
import six
from coolamqp.framing.definitions import ConnectionStart, ConnectionStartOk, \
    ConnectionTune, ConnectionTuneOk, ConnectionOpen, ConnectionOpenOk, ConnectionClose
from coolamqp.framing.frames import AMQPMethodFrame
from coolamqp.uplink.connection.states import ST_ONLINE


PUBLISHER_CONFIRMS = b'publisher_confirms'
CONSUMER_CANCEL_NOTIFY = b'consumer_cancel_notify'

SUPPORTED_EXTENSIONS = [
    PUBLISHER_CONFIRMS,
    CONSUMER_CANCEL_NOTIFY
]

CLIENT_DATA = [
        # because RabbitMQ is some kind of a fascist and does not allow
        # these fields to be of type short-string
        (b'product', (b'CoolAMQP', b'S')),
        (b'version', (b'develop', b'S')),
        (b'copyright', (b'Copyright (C) 2016-2017 DMS Serwis', b'S')),
        (b'information', (b'Licensed under the MIT License.\nSee https://github.com/smok-serwis/coolamqp for details', b'S')),
        (b'capabilities', ([(capa, (True, b't')) for capa in SUPPORTED_EXTENSIONS], b'F')),
      ]

WATCHDOG_TIMEOUT = 10


class Handshaker(object):
    """
    Object that given a connection rolls the handshake.
    """

    def __init__(self, connection, node_definition, on_success):
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
        self.connection.watch_for_method(0, ConnectionStart, self.on_connection_start)

        # Callbacks
        self.on_success = on_success

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

    def on_connection_start(self, payload):

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
        self.connection.watch_for_method(0, ConnectionTune, self.on_connection_tune)
        self.connection.send([
            AMQPMethodFrame(0,
                            ConnectionStartOk(CLIENT_DATA, b'PLAIN',
                                              b'\x00' + self.login + b'\x00' + self.password,
                                              locale_supported[0]
                                              ))
        ])

    def on_connection_tune(self, payload):
        self.connection.frame_max = payload.frame_max
        self.connection.heartbeat = min(payload.heartbeat, self.heartbeat)
        for channel in six.moves.xrange(1, (65535 if payload.channel_max == 0 else payload.channel_max)+1):
            self.connection.free_channels.append(channel)

        self.connection.watch_for_method(0, ConnectionOpenOk, self.on_connection_open_ok)
        self.connection.send([
            AMQPMethodFrame(0, ConnectionTuneOk(payload.channel_max, payload.frame_max, self.connection.heartbeat)),
            AMQPMethodFrame(0, ConnectionOpen(self.virtual_host))
        ])

        # Install heartbeat handlers NOW, if necessary
        if self.connection.heartbeat > 0:
            from coolamqp.uplink.heartbeat import Heartbeater
            Heartbeater(self.connection, self.connection.heartbeat)

    def on_connection_open_ok(self, payload):
        self.on_success()
