# coding=UTF-8
from __future__ import absolute_import, division, print_function
import uuid
from coolamqp.framing.frames import AMQPMethodFrame, AMQPBodyFrame, AMQPHeaderFrame
from coolamqp.framing.definitions import ChannelOpen, ChannelOpenOk, BasicConsume, \
    BasicConsumeOk, QueueDeclare, QueueDeclareOk, ExchangeDeclare, ExchangeDeclareOk, \
    QueueBind, QueueBindOk, ChannelClose, ChannelCloseOk, BasicCancel, BasicDeliver, \
    BasicAck, BasicReject, ACCESS_REFUSED, RESOURCE_LOCKED
from coolamqp.uplink import HeaderOrBodyWatch, MethodWatch


ST_OFFLINE = 0  # Consumer is *not* consuming, no setup attempts are being made
ST_SYNCING = 1  # A process targeted at consuming has been started
ST_ONLINE = 2   # Consumer is declared all right


class Consumer(object):
    """
    This object represents a consumer in the system.

    Consumer may reside on any AMQP broker, this is to be decided by CoolAMQP.
    Consumer, when created, has the state of ST_SYNCING. CoolAMQP will
    try to declare the consumer where it makes most sense for it to be.

    If it succeeds, the consumer will enter state ST_ONLINE, and callables
    on_start will be called. This means that broker has confirmed that this
    consumer is operational and receiving messages.

    If the consumer gets a message, it will relay it to a specified callable.
    The message may need acking or rejecting.

    THIS OBJECT CAN OUTLIVE IT'S BROKER, AND THEREFORE .broker FIELD MUST BE SET
    ON A NEW BROKER. HOWEVER, ALL WATCHES MUST BE CALLED BEFOREHAND.

    Note that does not attempt to cancel consumers, or any of such nonsense. Having
    a channel per consumer gives you the unique possibility of simply closing the channel.
    Since this implies cancelling the consumer, here you go.
    """

    def __init__(self, queue, no_ack=True, qos=None, dont_pause=False):
        """
        To be instantiated only by Cluster

        :param state: state of the consumer
        :param queue: Queue object, being consumed from right now.
            Note that name of anonymous queue might change at any time!
        :param no_ack: Will this consumer require acknowledges from messages?
        :param dont_pause: Consumer will fail on the spot instead of pausing
        """
        self.state = ST_OFFLINE
        self.queue = queue
        self.no_ack = no_ack

        # private
        self.broker = None  # broker on which was last seen
        self.channel_id = None

        self.cancelled = False  # did the client want to STOP using this consumer?

        # state machine for receiving messages
        self.recv_state = 0  # 0 - waiting for basic.deliver
                             # 1 - waiting for header
                             # 2 - waiting for body

        self.delivery = None    # tuple of (delivery tag, exchange, routing_key)
        self.properties = None
        self.content_parts = []
        self.length_remaining = 0

        self.remaining_for_ack = set() # unacknowledged delivery tags

    def on_header_or_body_or_delivery(self, frame):

        if isinstance(frame, BasicDeliver) and self.state == 0:
            self.delivery = frame.delivery_tag, frame.exchange, frame.routing_key
            self.recv_state = 1

        elif isinstance(frame, AMQPHeaderFrame) and self.state == 1:
            self.properties = frame.properties
            self.length_remaining = frame.body_size
            self.recv_state = 2

        elif isinstance(frame, AMQPBodyFrame) and self.state == 2:

            self.content_parts.append(frame.payload)
            self.length_remaining -= len(frame.payload)

            if self.length_remaining == 0:
                self.broker.on_new_message(self, self.delivery[0],
                                           self.delivery[1],
                                           self.delivery[2],
                                           self.properties,
                                           self.content_parts,
                                           not self.no_ack
                                           )
                if not self.no_ack:
                    self.remaining_for_ack.add(self.delivery[0])
                self.recv_state = 0
        else:
            self.broker.connection.send(None, 'state assertion failed')

    def reject(self, consumer, delivery_tag):

        if self.cancelled:
            return

        if self != consumer:
            return  # it was not me

        if delivery_tag not in self.remaining_for_ack:
            return  # not remaining

        self.broker.connection.send(AMQPMethodFrame(
            self.channel_id,
            BasicReject(delivery_tag, True)
        ))

        self.remaining_for_ack.remove(delivery_tag)

    def acknowledge(self, consumer, delivery_tag):

        if self.cancelled:
            return

        if self != consumer:
            return  # it was not me

        if delivery_tag not in self.remaining_for_ack:
            return  # not remaining

        self.broker.connection.send(AMQPMethodFrame(
            self.channel_id,
            BasicAck(delivery_tag, False)
        ))

        self.remaining_for_ack.remove(delivery_tag)

    def cancel(self):
        """Stop using this consumer"""
        self.cancelled = True

        if self.state == ST_ONLINE:
            # Consuming, close the channel please
            self.broker.connection.send(AMQPMethodFrame(self.channel_id,
                                                        ChannelClose(
                                                            0, 'Consumer cancelled', 0, 0
                                                        )))

    def on_close(self, payload=None):
        """Handle closing the channel. It sounds like an exception..."""

        if self.channel_id is None:
            return

        should_retry = False

        if isinstance(payload, ChannelClose):
            # it sounds like an exception
            self.broker.connection.send(AMQPMethodFrame(self.channel_id,
                                                        ChannelCloseOk()))

            should_retry = payload.reply_code in (ACCESS_REFUSED, RESOURCE_LOCKED)

        self.broker.connection.unwatch_all(self.channel_id)
        self.broker.free_channels.append(self.channel_id)
        self.channel_id = None
        self.state = ST_OFFLINE
        self.remaining_for_ack = set()
        self.recv_state = 0

        if should_retry:
            # retry
            self.on_uplink_established(self.broker)


    def on_setup(self, payload):
        """Called with different kinds of frames - during setup"""

        if self.cancelled:
            # We were declaring this, but during this situation this
            # consumer was cancelled. Close the channel and things.
            self.broker.connection.send(self.channel_id, ChannelClose(0, 'Consumer cancelled', 0, 0))
            return

        if isinstance(payload, ChannelOpenOk):
            # Do we need to declare the exchange?

            if self.queue.exchange is not None:
                self.broker.connection.method_and_watch(
                    self.channel_id,
                    ExchangeDeclare(self.queue.exchange.name.encode('utf8'),
                                    self.queue.exchange.type.encode('utf8'),
                                    False,
                                    self.queue.exchange.durable,
                                    self.queue.exchange.auto_delete,
                                    False,
                                    False,
                                    []),
                    ExchangeDeclareOk,
                    self.on_setup
                )
            else:
                self.on_setup(ExchangeDeclareOk())

        elif isinstance(payload, ExchangeDeclareOk):
            # Declare the queue

            name = b'' if self.queue.anonymous else self.queue.name.encode('utf8')

            self.broker.connection.method_and_watch(
                self.channel_id,
                QueueDeclare(
                    name,
                    False,
                    self.queue.durable,
                    self.queue.exclusive,
                    self.queue.auto_delete,
                    False,
                    []
                ),
                QueueDeclareOk,
                self.on_setup
            )

        elif isinstance(payload, QueueDeclareOk):
            # did we need an anonymous name?
            if self.queue.anonymous:
                self.queue.name = payload.queue_name.decode('utf8')

            # We need any form of binding.
            xchg_name = b'' if self.queue.exchange is None else self.queue.exchange.name.encode('utf8')

            self.broker.connection.method_and_watch(
                self.channel_id,
                QueueBind(
                    self.queue.name.encode('utf8'),
                    xchg_name,
                    b'',
                    False,
                    []
                ),
                QueueBindOk,
                self.on_setup
            )
        elif isinstance(payload, QueueBindOk):
            # itadakimasu
            self.broker.connection.method_and_watch(
                self.channel_id,
                BasicConsume(
                    self.queue.name.encode('utf8'),
                    self.queue.name.encode('utf8'),
                    False,
                    self.no_ack,
                    self.queue.exclusive,
                    False,
                    []
                ),
                BasicConsumeOk,
                self.on_setup
            )

        elif isinstance(payload, BasicConsumeOk):
            # AWWW RIGHT~!!!
            self.state = ST_ONLINE

            self.broker.connection.watch(HeaderOrBodyWatch(self.channel_id, self.on_header_or_body_or_delivery))
            mw = MethodWatch(self.channel_id, BasicDeliver, self.on_header_or_body_or_delivery)
            mw.oneshot = False
            self.broker.connection.watch(mw)

    def on_uplink_established(self, broker):
        """Consumer was created or uplink was regained. Try to declare it"""
        if self.cancelled:
            return  # it's OK.

        self.broker = broker

        self.state = ST_SYNCING
        self.channel_id = self.broker.free_channels.pop()

        self.broker.connection.watch_for_method(self.channel_id,
                                                (ChannelClose, ChannelCloseOk, BasicCancel),
                                                self.on_close,
                                                on_fail=self.on_close)

        self.broker.connection.method_and_watch(
            self.channel_id,
            ChannelOpen(),
            ChannelOpenOk,
            self.on_setup
        )
