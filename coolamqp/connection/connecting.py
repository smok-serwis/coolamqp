# coding=UTF-8
from __future__ import absolute_import, division, print_function
import logging
import six
from coolamqp.state.orders import BaseOrder
from coolamqp.framing.definitions import ChannelOpenOk, ChannelOpen
from coolamqp.framing.frames import AMQPMethodFrame
from coolamqp.uplink import Handshaker
from coolamqp.framing.extensions import PUBLISHER_CONFIRMS
"""
All the routines required to go from connecting to synced
"""

logger = logging.getLogger(__name__)


class ConnectingPeople(BaseOrder):
    def configure(self, broker, handshaker, connection, nodedef):
        self.handshaker = handshaker
        self.broker = broker
        self.connection = connection
        self.node_definition = nodedef

    def on_fail(self, reason):
        """Called at any time, by anything going wrong with basic init and sync"""
        self.set_exception(Exception(reason or 'Initialization failed'))

    def handshake_complete(self):
        """Called by handshaker, upon completing the initial frame exchange"""
        logger.info('%s:%s entered RANGING', self.node_definition.host, self.node_definition.port)
        self.broker.extensions = set(self.handshaker.extensions)
        if self.handshaker.channel_max < 2:
            self.connection.send(None, 'channel_max < 2 !!!')
            self.on_fail('channel_max < 2 !!')
            return

        for free_chan in six.moves.xrange(3, self.handshaker.channel_max + 1):
            self.broker.free_channels.append(free_chan)

        # It's OK, open channel 1 for sending messages
        self.connection.watch_for_method(1, ChannelOpenOk, self.send_nonconfirm_channel_opened)
        self.connection.send([AMQPMethodFrame(1, ChannelOpen())])

    def send_nonconfirm_channel_opened(self, payload):
        """Called upon opening channel #1, which is used for publishing messages without confirmation"""

        if PUBLISHER_CONFIRMS in self.handshaker.extensions:
            # We need to set up channel 2 with publisher confirms
            self.connection.watch_for_method(2, ChannelOpenOk, self.on_channel_2)
            self.connection.send([AMQPMethodFrame(2, ChannelOpen())])
        else:
            # Else we don't set up this channel
            self.on_syncing()

    def on_channel_2(self, payload):
        """Do things with Channel 2 - only if PUBLISHER_CONFIRMATION extension is enabled!"""
        from coolamqp.framing.definitions import ConfirmSelect, ConfirmSelectOk
        if isinstance(payload, ChannelOpenOk):
            # Ok, just opened the channel
            self.connection.watch_for_method(2, ConfirmSelectOk, self.on_channel_2)
            self.connection.send([AMQPMethodFrame(2, ConfirmSelect(False))])
        elif isinstance(payload, ConfirmSelectOk):
            # A-OK!
            logger.info('%s:%s entered SYNCING', self.node_definition.host, self.node_definition.port)

    def on_syncing(self):
        """We are entering SYNCING"""
        logger.info('%s:%s entered SYNCING', self.node_definition.host, self.node_definition.port)
        self.connection.on_connected()


