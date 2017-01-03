# coding=UTF-8
from __future__ import absolute_import, division, print_function
import monotonic

from coolamqp.framing.frames import AMQPHeartbeatFrame
from coolamqp.uplink.connection.watches import HeartbeatWatch

class Heartbeater(object):
    """
    An object that handles heartbeats
    """

    def __init__(self, connection, heartbeat_interval=0):
        self.connection = connection
        self.heartbeat_interval = heartbeat_interval

        self.last_heartbeat_on = monotonic.monotonic()  # last heartbeat from server

        self.connection.watchdog(self.heartbeat_interval, self.on_timer)
        self.connection.watch(HeartbeatWatch(self.on_heartbeat))

    def on_heartbeat(self):
        self.last_heartbeat_on = monotonic.monotonic()

    def on_timer(self):
        """Timer says we should send a heartbeat"""
        self.connection.send([AMQPHeartbeatFrame()])

        if (monotonic.monotonic() - self.last_heartbeat_on) > 2*self.heartbeat_interval:
            # closing because of heartbeat
            self.connection.send(None)

        self.connection.watchdog(self.heartbeat_interval, self.on_timer)

