# coding=UTF-8
"""
Base class for consumer or publisher with the capabiility to
set up and tear down channels
"""
from __future__ import print_function, absolute_import, division
import six
from coolamqp.framing.frames import AMQPMethodFrame, AMQPBodyFrame, AMQPHeaderFrame
from coolamqp.framing.definitions import ChannelOpen, ChannelOpenOk, BasicConsume, \
    BasicConsumeOk, QueueDeclare, QueueDeclareOk, ExchangeDeclare, ExchangeDeclareOk, \
    QueueBind, QueueBindOk, ChannelClose, ChannelCloseOk, BasicCancel, BasicDeliver, \
    BasicAck, BasicReject, ACCESS_REFUSED, RESOURCE_LOCKED, BasicCancelOk
from coolamqp.uplink import HeaderOrBodyWatch, MethodWatch


ST_OFFLINE = 0  # Consumer is *not* consuming, no setup attempts are being made
ST_SYNCING = 1  # A process targeted at consuming has been started
ST_ONLINE = 2   # Consumer is declared all right


class Channeler(object):
    """
    A base class for Consumer/Publisher implementing link set up and tear down.

    A channeler can be essentially in 4 states:
    - ST_OFFLINE (.channel is None): channel is closed, object is unusable. Requires an attach() a connection
                                     that is being established, or open, or whatever. Connection will notify
                                     this channeler that it's open.
    - ST_SYNCING: channeler is opening a channel/doing some other things related to it's setup.
                  it's going to be ST_ONLINE soon, or go back to ST_OFFLINE.
                  It has, for sure, acquired a channel number.
    - ST_ONLINE:  channeler is operational. It has a channel number and has declared everything
                  it needs to.

                  on_operational(True) will be called when a transition is made TO this state.
                  on_operational(False) will be called when a transition is made FROM this state.

    - ST_OFFLINE (.channel is not None): channeler is undergoing a close. It has not yet torn down the channel,
                                         but ordering it to do anything is pointless, because it will not get done
                                         until attach() with new connection is called.
    """

    def __init__(self):
        """
        [EXTEND ME!]
        """
        self.state = ST_OFFLINE
        self.connection = None
        self.channel_id = None      # channel obtained from Connection

    def attach(self, connection):
        """
        Attach this object to a live Connection.

        :param connection: Connection instance to use
        """
        self.connection = connection
        connection.call_on_connected(self.on_uplink_established)

    # ------- event handlers

    def on_operational(self, operational):
        """
        [EXTEND ME] Called by internal methods (on_*) when channel has achieved (or lost) operational status.

        If this is called with operational=True, then for sure it will be called with operational=False.

        This will, therefore, get called an even number of times.

        :param operational: True if channel has just become operational, False if it has just become useless.
        """

    def on_close(self, payload=None):
        """
        [EXTEND ME] Handler for channeler destruction.

        Called on:
        - channel exception
        - connection failing

        This handles following situations:
        - payload is None: this means that connection has gone down hard, so our Connection object is
                           probably very dead. Transition to ST_OFFLINE (.channel is None)
        - payload is a ChannelClose: this means that a channel exception has occurred. Dispatch a ChannelCloseOk,
                                     attempt to log an exception, transition to ST_OFFLINE (.channel is None)
        - payload is a ChannelCloseOk: this means that it was us who attempted to close the channel. Return the channel
                                       to free pool, transition to ST_OFFLINE (.channel is None)

        If you need to handle something else, extend this. Take care that this DOES NOT HANDLE errors that happen
        while state is ST_SYNCING. You can expect this to handle a full channel close, therefore releasing all
        resources, so it mostly will do *the right thing*.

        If you need to do something else than just close a channel, please extend or modify as necessary.

        """
        if self.state == ST_ONLINE:
            # The channel has just lost operationality!
            self.on_operational(False)
        self.state = ST_OFFLINE

        if payload is None:
            # Connection went down HARD
            self.connection.free_channels.put(self.channel_id)
            self.channel_id = None
        elif isinstance(payload, ChannelClose):
            # We have failed
            print('Channel close: RC=%s RT=%s', payload.reply_code, payload.reply_text)
            self.connection.free_channels.put(self.channel_id)
            self.channel_id = None

        elif isinstance(payload, ChannelCloseOk):
            self.connection.free_channels.put(self.channel_id)
            self.channel_id = None
        else:
            raise Exception('Unrecognized payload - did you forget to handle something? :D')

    def methods(self, payloads):
        """
        Syntactic sugar for

            for payload in paylods:
                self.method(payload)

        But moar performant.
        """
        assert self.channel_id is not None
        frames = [AMQPMethodFrame(self.channel_id, payload) for payload in payloads]
        self.connection.send(frames)

    def method(self, payload):
        """
        Syntactic sugar for:

            self.connection.send([AMQPMethodFrame(self.channel_id, payload)])
        """
        self.methods([payload])

    def method_and_watch(self, method_payload, method_classes_to_watch, callable):
        """
        Syntactic sugar for

            self.connection.method_and_watch(self.channel_id,
                                             method_payload,
                                             method_classes_to_watch,
                                             callable)
        """
        assert self.channel_id is not None
        self.connection.method_and_watch(self.channel_id, method_payload, method_classes_to_watch, callable)

    def on_setup(self, payload):
        """
        [OVERRIDE ME!] Called with a method frame that signifies a part of setup.

        You must be prepared to handle at least a payload of ChannelOpenOk

        :param payload: AMQP method frame payload
        """
        raise Exception('Abstract method - override me!')


    def on_uplink_established(self):
        """Called by connection. Connection reports being ready to do things."""
        self.state = ST_SYNCING
        self.channel_id = self.connection.free_channels.pop()

        self.connection.watch_for_method(self.channel_id, (ChannelClose, ChannelCloseOk, BasicCancel),
                                         self.on_close,
                                         on_fail=self.on_close)

        self.connection.method_and_watch(
            self.channel_id,
            ChannelOpen(),
            ChannelOpenOk,
            self.on_setup
        )

