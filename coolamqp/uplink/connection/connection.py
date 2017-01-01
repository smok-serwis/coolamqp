# coding=UTF-8
from __future__ import absolute_import, division, print_function
import logging
import collections
from coolamqp.uplink.listener import ListenerThread

from coolamqp.uplink.connection.recv_framer import ReceivingFramer
from coolamqp.uplink.connection.send_framer import SendingFramer
from coolamqp.framing.frames import AMQPMethodFrame, AMQPHeartbeatFrame

from coolamqp.uplink.connection.watches import MethodWatch, FailWatch

logger = logging.getLogger(__name__)


class Connection(object):
    """
    An object that manages a connection in a comprehensive way.

    It allows for sending and registering watches for particular things.
    """

    def __init__(self, socketobject, listener_thread):
        self.listener_thread = listener_thread
        self.socketobject = socketobject
        self.recvf = ReceivingFramer(self.on_frame)
        self.failed = False
        self.transcript = None

        self.watches = {}    # channel => [Watch object]
        self.fail_watches = []

    def start(self):
        """
        Start processing events for this connect
        :return:
        """
        self.listener_socket = self.listener_thread.register(self.socketobject,
                                                            on_read=self.recvf.put,
                                                            on_fail=self.on_fail)
        self.sendf = SendingFramer(self.listener_socket.send)

    def on_fail(self):
        """Underlying connection is closed"""
        if self.transcript is not None:
            self.transcript.on_fail()

        for channel, watches in self.watches:
            for watch in watches:
                watch.failed()

        self.watches = {}

        for watch in self.fail_watches:
            watch.fire()

        self.fail_watches = []

        self.failed = True

    def send(self, frames, reason=None):
        """
        :param frames: list of frames or None to close the link
        :param reason: optional human-readable reason for this action
        """
        if not self.failed:
            if frames is not None:
                self.sendf.send(frames)
                if self.transcript is not None:
                    for frame in frames:
                        self.transcript.on_send(frame, reason)
            else:
                self.listener_socket.send(None)
                self.failed = True

                if self.transcript is not None:
                    self.transcript.on_close_client(reason)

    def on_frame(self, frame):
        if self.transcript is not None:
            self.transcript.on_frame(frame)

        if frame.channel in self.watches:
            deq = self.watches[frame.channel]

            examined_watches = []
            while len(deq) > 0:
                watch = deq.popleft()
                if not watch.is_triggered_by(frame) or (not watch.oneshot):
                    examined_watches.append(watch)

            for watch in reversed(examined_watches):
                deq.appendleft(watch)

        logger.critical('Unhandled frame %s, dropping', frame)

    def watch_watchdog(self, delay, callback):
        """
        Call callback in delay seconds. One-shot.
        """
        self.listener_socket.oneshot(delay, callback)

    def watch(self, watch):
        """
        Register a watch.
        :param watch: Watch to register
        """
        if isinstance(watch, FailWatch):
            self.fail_watches.append(watch)
        else:
            if watch.channel not in self.watches:
                self.watches[watch.channel] = collections.deque([watch])
            else:
                self.watches[watch.channel].append(watch)

    def watch_for_method(self, channel, method, callback):
        """
        :param channel: channel to monitor
        :param method: AMQPMethodPayload class
        :param callback: callable(AMQPMethodPayload instance)
        """
        self.watch(MethodWatch(channel, method, callback))
