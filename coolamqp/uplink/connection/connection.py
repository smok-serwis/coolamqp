# coding=UTF-8
from __future__ import absolute_import, division, print_function
import logging
import collections
from coolamqp.uplink.listener import ListenerThread

from coolamqp.uplink.connection.recv_framer import ReceivingFramer
from coolamqp.uplink.connection.send_framer import SendingFramer
from coolamqp.framing.frames import AMQPMethodFrame, AMQPHeartbeatFrame


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

        self.method_watches = {}    # channel => [AMQPMethodPayload instance, callback]

        # to call if an unwatched frame is caught
        self.on_heartbeat = lambda: None
        self.unwatched_frame = lambda frame: None  # callable(AMQPFrame instance)

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
        if self.transcript is not None:
            self.transcript.on_fail()
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

        if isinstance(frame, AMQPMethodFrame):
            if frame.channel in self.method_watches:
                if isinstance(frame.payload, self.method_watches[frame.channel][0]):
                    method, callback = self.method_watches[frame.channel].popleft()
                    callback(frame.payload)
                    return

        if isinstance(frame, AMQPHeartbeatFrame):
            self.on_heartbeat()
            return

        self.unwatched_frame(frame)

    def watch_watchdog(self, delay, callback):
        """
        Call callback in delay seconds. One-shot.
        """
        self.listener_socket.oneshot(delay, callback)

    def watch_for_method(self, channel, method, callback):
        """
        :param channel: channel to monitor
        :param method: AMQPMethodPayload class
        :param callback: callable(AMQPMethodPayload instance)
        """
        if channel not in self.method_watches:
            self.method_watches[channel] = collections.deque()
        self.method_watches[channel].append((method, callback))