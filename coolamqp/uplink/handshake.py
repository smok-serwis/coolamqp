# coding=UTF-8
from __future__ import absolute_import, division, print_function
"""
Provides reactors that can authenticate an AQMP session
"""

from coolamqp.framing.definitions import ConnectionStart, ConnectionStartOk, \
    ConnectionTune, ConnectionTuneOk, ConnectionOpen, ConnectionOpenOk
from coolamqp.framing.frames import AMQPMethodFrame

ST_AWAITING_CONNECTIONSTART = 0
ST_CONNECTIONSTARTOK_SENT = 1

CLIENT_DATA = [
        # because RabbitMQ is some kind of a fascist and does not allow
        # these fields to be of type short-string
        (b'product', (b'CoolAMQP', b'S')),
        (b'version', (b'develop', b'S')),
        (b'copyright', (b'Copyright (C) 2016-2017 DMS Serwis', b'S')),
        (b'information', (b'Licensed under the MIT License.\nSee https://github.com/smok-serwis/coolamqp for details', b'S')),
        (b'capabilities', ([
                               (b'consumer_cancel_notify', (True, b't')),
                               (b'connection.blocked', (True, b't'))
            ], b'F'))
      ]


class Handshaker(object):
    """
    Object that given a connection rolls the handshake.
    """

    def __init__(self, connection, login, password, virtual_host,
                 on_success, on_fail, heartbeat=0):
        """
        :param connection: Connection instance to use
        :param login: login to try
        :param password: password to try
        :param virtual_host: virtual_host to pick
        :param on_success: callable/0, on success
        :param on_fail: callable/0, on failure
        :param heartbeat: heartbeat to requisition
        """
        self.connection = connection
        self.login = login
        self.password = password
        self.virtual_host = virtual_host
        self.connection.watch_for_method(0, ConnectionStart, self.on_connection_start)

        # Callbacks
        self.on_success = on_success
        self.on_fail = on_fail

        # Negotiated parameters
        self.channel_max = None
        self.frame_max = None
        self.heartbeat = heartbeat

        self.connected = False

    def on_watchdog(self):
        if not self.connected:
            # Not connected in 20 seconds - abort
            self.connection.send(None, 'connection not established within 20 seconds')
            self.on_fail()

    def on_connection_start(self, payload):
        sasl_mechanisms = payload.mechanisms.split(b' ')
        locale_supported = payload.locales.split(b' ')

        # Select a mechanism
        if b'PLAIN' not in sasl_mechanisms:
            raise ValueError('Server does not support PLAIN')

        self.connection.watch_watchdog(20, self.on_watchdog)
        self.connection.watch_for_method(0, ConnectionTune, self.on_connection_tune)
        self.connection.send([
            AMQPMethodFrame(0,
                            ConnectionStartOk(CLIENT_DATA, b'PLAIN',
                                              b'\x00' + self.login.encode('utf8') + b'\x00' + self.password.encode(
                                                  'utf8'),
                                              locale_supported[0]
                                              ))
        ], 'connecting')

    def on_connection_tune(self, payload):
        print('Channel max: ', payload.channel_max, 'Frame max: ', payload.frame_max, 'Heartbeat: ', payload.heartbeat)

        self.channel_max = 65535 if payload.channel_max == 0 else payload.channel_max
        self.frame_max = payload.frame_max
        self.heartbeat = min(payload.heartbeat, self.heartbeat)

        self.connection.watch_for_method(0, ConnectionOpenOk, self.on_connection_open_ok)
        self.connection.send([
            AMQPMethodFrame(0, ConnectionTuneOk(self.channel_max, self.frame_max, self.heartbeat)),
            AMQPMethodFrame(0, ConnectionOpen(self.virtual_host))
        ], 'connecting')

        # Install heartbeat handlers NOW, if necessary
        if self.heartbeat > 0:
            from coolamqp.uplink.heartbeat import Heartbeater
            Heartbeater(self.connection, self.heartbeat)

    def on_connection_open_ok(self, payload):
        print('Connection opened OK!')
        self.on_success()
        self.connected = True
