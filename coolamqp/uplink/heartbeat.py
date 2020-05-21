# coding=UTF-8
from __future__ import absolute_import, division, print_function

import typing as tp

from coolamqp.utils import monotonic

from coolamqp.framing.frames import AMQPHeartbeatFrame
from coolamqp.uplink.connection.watches import AnyWatch


class Heartbeater(object):
    """
    An object that handles heartbeats
    """

    def __init__(self, connection,  # type: coolamqp.uplink.connection.Connection
                 heartbeat_interval=0  # type: tp.Union[int, float]
                 ):
        self.connection = connection
        self.heartbeat_interval = heartbeat_interval

        self.last_heartbeat_on = monotonic()  # last heartbeat from server

        self.connection.watchdog(self.heartbeat_interval, self.on_timer)
        self.connection.watch(AnyWatch(self.on_heartbeat))

    def on_heartbeat(self, frame):
        self.last_heartbeat_on = monotonic()

    def on_any_frame(self):
        """
        Hehehe, most AMQP servers are not AMQP-compliant.
        Consider a situation where you just got like a metric shitton of messages,
        and the TCP connection is bustin' filled with those frames.

        Server should still be able to send a heartbeat frame, but it doesn't, because of the queue, and
        BANG, dead.

        I know I'm being picky, but at least I implement this behaviour correctly - see priority argument in send.

        Anyway, we should register an all-watch for this.
        """
        self.last_heartbeat_on = monotonic()

    def on_timer(self):
        """Timer says we should send a heartbeat"""
        self.connection.send([AMQPHeartbeatFrame()], priority=True)

        if (
                monotonic() - self.last_heartbeat_on) > 2 * self.heartbeat_interval:
            # closing because of heartbeat
            self.connection.send(None)

        self.connection.watchdog(self.heartbeat_interval, self.on_timer)
