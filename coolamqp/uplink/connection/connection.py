# coding=UTF-8
from __future__ import absolute_import, division, print_function
import logging
import collections
from coolamqp.uplink.listener import ListenerThread

from coolamqp.uplink.connection.recv_framer import ReceivingFramer
from coolamqp.uplink.connection.send_framer import SendingFramer
from coolamqp.framing.frames import AMQPMethodFrame


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

        self.method_watches = {}    # channel => [AMQPMethodPayload instance, callback]

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
        self.failed = True

    def send(self, frames):
        """
        :param frames: list of frames or None to close the link
        """
        if not self.failed:
            if frames is not None:
                self.sendf.send(frames)
            else:
                self.listener_socket.send(None)
                self.failed = True

    def on_frame(self, frame):
        if isinstance(frame, AMQPMethodFrame):
            if frame.channel in self.method_watches:
                if isinstance(frame.payload, self.method_watches[frame.channel][0]):
                    method, callback = self.method_watches[frame.channel].popleft()
                    callback(frame.payload)


    def watch_for_method(self, channel, method, callback):
        """
        :param channel: channel to monitor
        :param method: AMQPMethodPayload class
        :param callback: callable(AMQPMethodPayload instance)
        """
        if channel not in self.method_watches:
            self.method_watches[channel] = collections.deque()
        self.method_watches[channel].append((method, callback))