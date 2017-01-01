# coding=UTF-8
from __future__ import absolute_import, division, print_function
import monotonic

from coolamqp.framing.frames import AMQPHeartbeatFrame


class Heartbeater(object):
    """
    An object that handles heartbeats
    """

    def __init__(self, connection, heartbeat_interval=0):
        self.connection = connection
        self.heartbeat_interval = heartbeat_interval

        self.last_heartbeat_on = monotonic.monotonic()  # last heartbeat from server

        self.connection.watch_watchdog(self.heartbeat_interval, self.on_timer)
        self.connection.on_heartbeat = self.on_heartbeat

    def on_heartbeat(self):
        self.last_heartbeat_on = monotonic.monotonic()

    def on_timer(self):
        """Timer says we should send a heartbeat"""
        self.connection.send([AMQPHeartbeatFrame()], 'heartbeat')

        if (monotonic.monotonic() - self.last_heartbeat_on) > 2*self.heartbeat_interval:
            # closing because of heartbeat
            self.connection.send(None, 'heartbeat expired')

        self.connection.watch_watchdog(self.heartbeat_interval, self.on_timer)

