# coding=UTF-8
from __future__ import absolute_import, division, print_function
import uuid
from coolamqp.framing.frames import AMQPMethodFrame, AMQPBodyFrame, AMQPHeaderFrame
from coolamqp.framing.definitions import ChannelOpen, ChannelOpenOk, BasicConsume, \
    BasicConsumeOk, QueueDeclare, QueueDeclareOk, ExchangeDeclare, ExchangeDeclareOk, \
    QueueBind, QueueBindOk, ChannelClose, ChannelCloseOk, BasicCancel, BasicDeliver, \
    BasicAck, BasicReject, ACCESS_REFUSED, RESOURCE_LOCKED, BasicCancelOk
from coolamqp.uplink import HeaderOrBodyWatch, MethodWatch


ST_OFFLINE = 0  # Consumer is *not* consuming, no setup attempts are being made
ST_SYNCING = 1  # A process targeted at consuming has been started
ST_ONLINE = 2   # Consumer is declared all right


EV_ONLINE = 0   # called upon consumer being online and consuming
EV_CANCEL = 1   # consumer has been cancelled by BasicCancel.
                # EV_OFFLINE will follow immediately
EV_OFFLINE = 2  # channel down
EV_MESSAGE = 3  # received a message

class Consumer(object):
    """
    This object represents a consumer in the system.

    Consumer may reside on any AMQP broker, this is to be decided by CoolAMQP.
    Consumer, when created, has the state of ST_SYNCING. CoolAMQP will
    try to declare the consumer where it makes most sense for it to be.

    If it succeeds, the consumer will enter state ST_ONLINE, and callables
    on_start will be called. This means that broker has confirmed that this
    consumer is operational and receiving messages.

    Note that does not attempt to cancel consumers, or any of such nonsense. Having
    a channel per consumer gives you the unique possibility of simply closing the channel.
    Since this implies cancelling the consumer, here you go.
    """

    def attach(self, connection):
        """
        Attach this consumer to a connection
        :param connection: coolamqp.framing.Connection
        """
        self.connection = connection
        connection.call_on_connected(self.on_uplink_established)

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
        self.connection = None  # broker on which was last seen
        self.channel_id = None
        self.cancelled = False  # did the client want to STOP using this consumer?
        self.receiver = None  # MessageReceiver instance


    def on_event(self, event, arg=None):
        """
        Called upon events arriving. Possible events are:
        arg={EV_ONLINE} called directly after setup. self.state is not yet set!
        args={EV_CANCEL} seen a RabbitMQ consumer cancel notify. EV_OFFLINE follows
        args={EV_OFFLINE} sent when a channel is no longer usable. It may not yet have been torn down.
        arg={EV_MESSAGE}
        """
        if event == EV_OFFLINE and (self.state is not ST_ONLINE):
            return # No point in processing that

        if event == EV_ONLINE:
            self.state = ST_ONLINE
            assert self.receiver is None
            self.receiver = MessageReceiver(self)

        elif event == EV_OFFLINE:
            self.receiver = None

    def __stateto(self, st):
        """if st is not current state, statify it.
        As an extra if it's a transition to ST_OFFLINE, send an event"""
        if (self.state != ST_OFFLINE) and (st == ST_OFFLINE):
            self.on_event(ST_OFFLINE)
        else:
            self.state = st

    def on_close(self, payload=None):
        """
        Handle closing the channel. It sounds like an exception...

        This is done in two steps:
        1. self.state <- ST_OFFLINE, on_event(EV_OFFLINE)   upon detecting that no more messages will
           be there
        2. self.channel_id <- None, channel is returned to Connection - channel has been physically torn down
        """
        should_retry = False
        release_channel = False

        if isinstance(payload, BasicCancel):
            # Consumer Cancel Notification - by RabbitMQ
            self.on_event(EV_CANCEL)
            self.__stateto(ST_OFFLINE)
            self.connection.send([AMQPMethodFrame(self.channel_id, BasicCancelOk()),
                                  AMQPMethodFrame(self.channel_id, ChannelClose(0, b'Received basic.cancel', 0, 0))])
            return

        if isinstance(payload, BasicCancelOk):
            self.__stateto(ST_OFFLINE)
            # proceed with teardown
            self.connection.send([AMQPMethodFrame(self.channel_id, ChannelClose(0, b'Received basic.cancel-ok', 0, 0))])
            return

        # at this point this can be only ChannelClose, ChannelCloseOk or on_fail
        # release the kraken

        if isinstance(payload, ChannelClose):
            # it sounds like an exception
            self.__stateto(ST_OFFLINE)
            print(payload.reply_code, payload.reply_text)
            self.connection.send([AMQPMethodFrame(self.channel_id, ChannelCloseOk())])
            should_retry = payload.reply_code in (ACCESS_REFUSED, RESOURCE_LOCKED)

        if self.channel_id is not None:
            self.__stateto(ST_OFFLINE)
            self.connection.unwatch_all(self.channel_id)
            self.connection.free_channels.append(self.channel_id)
            self.channel_id = None
            self.remaining_for_ack = set()

        if should_retry:
            self.on_uplink_established() # retry

    def on_delivery(self, sth):
        """
        Callback for delivery-related shit
        :param sth: AMQPMethodFrame WITH basic-deliver, AMQPHeaderFrame or AMQPBodyFrame
        """
        if isinstance(sth, BasicDeliver):
            self.receiver.on_basic_deliver(sth)
        elif isinstance(sth, AMQPBodyFrame):
            self.receiver.on_body(sth.data)
        elif isinstance(sth, AMQPHeaderFrame):
            self.receiver.on_head(sth)

        # No point in listening for more stuff, that's all the watches even listen for

    def on_setup(self, payload):
        """Called with different kinds of frames - during setup"""

        if self.cancelled:
            # We were declaring this, but during this situation this
            # consumer was cancelled. Close the channel and things.
            self.connection.send(self.channel_id, ChannelClose(0, 'Consumer cancelled', 0, 0))
            return

        if isinstance(payload, ChannelOpenOk):
            # Do we need to declare the exchange?

            if self.queue.exchange is not None:
                self.connection.method_and_watch(
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

            self.connection.method_and_watch(
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
            if self.queue.exchange is not None:
                self.connection.method_and_watch(
                    self.channel_id,
                    QueueBind(
                        self.queue.name.encode('utf8'),
                        self.queue.exchange.name.encode('utf8'),
                        b'',
                        False,
                        []
                    ),
                    QueueBindOk,
                    self.on_setup
                )
            else:
                # default exchange, pretend it was bind ok
                self.on_setup(QueueBindOk())
        elif isinstance(payload, QueueBindOk):
            # itadakimasu
            self.connection.method_and_watch(
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

            # Register watches for receiving shit
            self.connection.watch(HeaderOrBodyWatch(self.channel_id, self.on_delivery))
            mw = MethodWatch(self.channel_id, BasicDeliver, self.on_delivery)
            mw.oneshot = False
            self.connection.watch(mw)

            self.on_event(EV_ONLINE)

    def on_uplink_established(self):
        """Consumer was created or uplink was regained. Try to declare it"""
        if self.cancelled:
            return  # it's OK.

        self.state = ST_SYNCING
        self.channel_id = self.connection.free_channels.pop()

        self.connection.watch_for_method(self.channel_id,
                                         (ChannelClose, ChannelCloseOk, BasicCancel),
                                         self.on_close,
                                         on_fail=self.on_close)

        self.connection.method_and_watch(
            self.channel_id,
            ChannelOpen(),
            ChannelOpenOk,
            self.on_setup
        )



class MessageReceiver(object):
    """This is an object that is used to received messages.

    It maintains all the state, and is used to ack/nack messages as well.

    This object is TORN DOWN when a consumer goes offline,
    and is recreated when it goes online.

    This is called by consumer upon receiving different parts of the message,
    and may opt to kill the connection on bad framing with
    self.consumer.connection.send(None)
    """
    def __init__(self, consumer):
        self.consumer = consumer
        self.state = 0  # 0 - waiting for Basic-Deliver
                        # 1 - waiting for Header
                        # 2 - waiting for Body [all]

        self.bdeliver = None    # payload of Basic-Deliver
        self.header = None      # AMQPHeaderFrame
        self.body = []          # list of payloads
        self.data_to_go = None  # set on receiving header, how much bytes we need yet

    def on_head(self, frame):
        assert self.state == 1
        self.header = frame
        self.data_to_go = frame.body_size
        self.state = 2

    def on_basic_deliver(self, payload):
        assert self.state == 0
        self.bdeliver = payload
        self.state = 1

    def on_body(self, payload):
        assert self.state == 2
        self.body.append(payload)
        self.data_to_go -= len(payload)
        assert self.data_to_go >= 0
        if self.data_to_go == 0:
            # Message A-OK!
            print('Yo, got a message of %s' % (u''.join(map(str, self.body))))
            self.state = 0

        # at this point it's safe to clear the body
        self.body = []
