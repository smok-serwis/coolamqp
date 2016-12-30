# coding=UTF-8
from __future__ import absolute_import, division, print_function
import logging
from coolamqp.uplink.listener import ListenerThread

from coolamqp.uplink.connection.recv_framer import ReceivingFramer
from coolamqp.uplink.connection.send_framer import SendingFramer


logger = logging.getLogger(__name__)


class Connection(object):
    """
    An object that manages a connection in a comprehensive way
    """

    def __init__(self, socketobject, listener_thread, reactor=None):
        self.reactor = reactor
        if reactor is None:
            logger.warn('Creating connection without a reactor; hope you know what you''re doing')
        else:
            reactor.set_send_frame(self.send)

        self.recvf = ReceivingFramer(self.on_frame)
        self.failed = False

        self.listener_socket = listener_thread.register(socketobject,
                                                        on_read=self.recvf.put,
                                                        on_fail=self.on_fail)

        self.sendf = SendingFramer(self.listener_socket.send)

    def set_reactor(self, reactor):
        self.reactor = reactor
        reactor.set_send_frame(self.send)

    def on_fail(self):
        self.failed = True
        self.reactor.on_close()

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
        if self.reactor is None:
            logger.warn('Received %s but no reactor present. Dropping.', frame)
        else:
            self.reactor.on_frame(frame)

