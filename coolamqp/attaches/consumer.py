# coding=UTF-8
from __future__ import absolute_import, division, print_function
import six
import logging
from coolamqp.framing.frames import AMQPBodyFrame, AMQPHeaderFrame
from coolamqp.framing.definitions import ChannelOpenOk, BasicConsume, \
    BasicConsumeOk, QueueDeclare, QueueDeclareOk, ExchangeDeclare, ExchangeDeclareOk, \
    QueueBind, QueueBindOk, ChannelClose, BasicCancel, BasicDeliver, \
    BasicAck, BasicReject, RESOURCE_LOCKED, BasicCancelOk, BasicQos, HARD_ERROR
from coolamqp.uplink import HeaderOrBodyWatch, MethodWatch

from coolamqp.attaches.channeler import Channeler, ST_ONLINE, ST_OFFLINE
from coolamqp.exceptions import ResourceLocked, AMQPError


logger = logging.getLogger(__name__)


class Consumer(Channeler):
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

    def __init__(self, queue, on_message, no_ack=True, qos=None, cancel_on_failure=False,
                 future_to_notify=None,
                 fail_on_first_time_resource_locked=False
                 ):
        """
        :param queue: Queue object, being consumed from right now.
            Note that name of anonymous queue might change at any time!
        :param on_message: callable that will process incoming messages
        :type on_message: callable(ReceivedMessage instance)
        :param no_ack: Will this consumer require acknowledges from messages?
        :param qos: a tuple of (prefetch size, prefetch window) for this consumer
        :type qos: tuple(int, int) or tuple(None, int)
        :param cancel_on_failure: Consumer will cancel itself when link goes down
        :type cancel_on_failure: bool
        :param future_to_notify: Future to succeed when this consumer goes online for the first time.
                                 This future can also raise with:
                                        AMQPError - a HARD_ERROR (see AMQP spec) was encountered
                                        ResourceLocked - this was the first declaration, and
                                            fail_on_first_time_resource_locked was set
        :param fail_on_first_time_resource_locked: When consumer is declared for the first time,
                                                   and RESOURCE_LOCKED is encountered, it will fail the
                                                   future with ResourceLocked, and consumer will cancel itself.
                                                   By default it will retry until success is made.
                                                   If the consumer doesn't get the chance to be declared - because
                                                   of a connection fail - next reconnect will consider this to be
                                                   SECOND declaration, ie. it will retry ad infinitum
        :type fail_on_first_time_resource_locked: bool
        """
        super(Consumer, self).__init__()

        self.queue = queue
        self.no_ack = no_ack

        self.on_message = on_message

        # private
        self.cancelled = False  # did the client want to STOP using this consumer?
        self.receiver = None  # MessageReceiver instance

        self.attache_group = None   # attache group this belongs to.
                                    # if this is not None, then it has an attribute
                                    # on_cancel_customer(Consumer instance)
        if qos is not None:
            if qos[0] is None:
                qos = 0, qos[1] # prefetch_size=0=undefined
        self.qos = qos
        self.qos_update_sent = False    # QoS was not sent to server

        self.future_to_notify = future_to_notify
        self.fail_on_first_time_resource_locked = fail_on_first_time_resource_locked
        self.cancel_on_failure = cancel_on_failure

    def set_qos(self, prefetch_size, prefetch_count):
        """
        Set new QoS for this consumer.

        :param prefetch_size: prefetch in octets
        :param prefetch_count: prefetch in whole messages
        """
        if self.state == ST_ONLINE:
            self.method(BasicQos(prefetch_size or 0, prefetch_count, False))
        self.qos = prefetch_size or 0, prefetch_count

    def cancel(self):
        """
        Cancel the customer.

        Note that this is a departure form AMQP specification. We don't attempt to cancel the customer,
        we simply trash the channel. Idk if it's a good idea...

        .ack() or .nack() for messages from this customer will have no effect.
        """
        self.cancelled = True
        self.method(ChannelClose(0, b'consumer cancelled', 0, 0))
        if self.attache_group is not None:
            self.attache_group.on_cancel_customer(self)


    def on_operational(self, operational):
        super(Consumer, self).on_operational(operational)

        if operational:
            assert self.receiver is None
            self.receiver = MessageReceiver(self)

            # notify the future
            if self.future_to_notify is not None:
                self.future_to_notify.set_result()
                self.future_to_notify = None

        else:
            self.receiver.on_gone()
            self.receiver = None

    def on_close(self, payload=None):
        """
        Handle closing the channel. It sounds like an exception...

        This is done in two steps:
        1. self.state <- ST_OFFLINE, on_event(EV_OFFLINE)   upon detecting that no more messages will
           be there
        2. self.channel_id <- None, channel is returned to Connection - channel has been physically torn down

        Note, this can be called multiple times, and eventually with None.

        """

        if self.cancel_on_failure:
            logger.debug('Consumer is cancel_on_failure and failure seen, cancelling')
            self.cancel()

        if self.state == ST_ONLINE:
            # The channel has just lost operationality!
            self.on_operational(False)
        self.state = ST_OFFLINE

        should_retry = False

        if isinstance(payload, BasicCancel):
            # Consumer Cancel Notification - by RabbitMQ
            self.methods([BasicCancelOk(), ChannelClose(0, b'Received basic.cancel', 0, 0)])
            return

        if isinstance(payload, BasicCancelOk):
            # OK, our cancelling went just fine - proceed with teardown
            self.method(ChannelClose(0, b'Received basic.cancel-ok', 0, 0))
            return

        if isinstance(payload, ChannelClose):
            rc = payload.reply_code
            if rc == RESOURCE_LOCKED:
                # special handling
                # This is because we might be reconnecting, and the broker doesn't know yet that we are dead.
                # it won't release our exclusive channels, and that's why we'll get RESOURCE_LOCKED.

                if self.fail_on_first_time_resource_locked:
                    # still, a RESOURCE_LOCKED on a first declaration ever suggests something is very wrong
                    if self.future_to_notify:
                        self.future_to_notify.set_exception(ResourceLocked(payload))
                        self.future_to_notify = None
                        self.cancel()

                should_retry = True
            elif rc in HARD_ERROR:
                logger.warn('Channel closed due to hard error, %s: %s', payload.reply_code, payload.reply_text)
                if self.future_to_notify:
                    self.future_to_notify.set_exception(AMQPError(payload))
                    self.future_to_notify = None


        # We might not want to throw the connection away.
        should_retry = should_retry and (not self.cancelled)


        old_con = self.connection

        super(Consumer, self).on_close(payload)     # this None's self.connection
        self.fail_on_first_time_resource_locked = False

        if should_retry:
            if old_con.state == ST_ONLINE:
                logger.info('Retrying with %s', self.queue.name)
                self.attach(old_con)

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
                self.method_and_watch(
                    QueueBind(
                        self.queue.name.encode('utf8'), self.queue.exchange.name.encode('utf8'),
                        b'', False, []),
                    QueueBindOk,
                    self.on_setup
                )
            else:
                # default exchange, pretend it was bind ok
                self.on_setup(QueueBindOk())
        elif isinstance(payload, QueueBindOk):
            # itadakimasu
            if self.qos is not None:
                self.method(BasicQos(self.qos[0], self.qos[1], False))
            self.method_and_watch(
                BasicConsume(self.queue.name.encode('utf8'), self.queue.name.encode('utf8'),
                    False, self.no_ack, self.queue.exclusive, False, []),
                BasicConsumeOk,
                self.on_setup
            )

        elif isinstance(payload, BasicConsumeOk):
            # AWWW RIGHT~!!! We're good.

            # Register watches for receiving shit
            self.connection.watch(HeaderOrBodyWatch(self.channel_id, self.on_delivery))
            mw = MethodWatch(self.channel_id, BasicDeliver, self.on_delivery)
            mw.oneshot = False
            self.connection.watch(mw)

            self.state = ST_ONLINE
            self.on_operational(True)

            # resend QoS, in case of sth
            if self.qos is not None:
                self.set_qos(self.qos[0], self.qos[1])


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
                        # 3 - gone!

        self.bdeliver = None    # payload of Basic-Deliver
        self.header = None      # AMQPHeaderFrame
        self.body = []          # list of payloads
        self.data_to_go = None  # set on receiving header, how much bytes we need yet

        self.acks_pending = set()   # list of things to ack/reject

    def on_gone(self):
        """Called by Consumer to inform upon discarding this receiver"""
        self.state = 3

    def confirm(self, delivery_tag, success):
        """
        This crafts a constructor for confirming messages.

        This should return a callable/0, whose calling will ACK or REJECT the message.
        Calling it multiple times should have no ill effect.

        If this receiver is long gone,

        :param delivery_tag: delivery_tag to ack
        :param success: True if ACK, False if REJECT
        :return: callable/0
        """

        def callable():
            if self.state == 3:
                return  # Gone!

            if self.consumer.cancelled:
                return # cancelled!

            if delivery_tag not in self.acks_pending:
                return  # already confirmed/rejected

            if success:
                self.consumer.method(BasicAck(delivery_tag, False))
            else:
                self.consumer.method(BasicReject(delivery_tag, True))

        return callable


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
        """:type payload: buffer"""
        assert self.state == 2
        self.body.append(payload)
        self.data_to_go -= len(payload)
        assert self.data_to_go >= 0
        if self.data_to_go == 0:
            ack_expected = not self.consumer.no_ack

            # Message A-OK!

            if ack_expected:
                self.acks_pending.add(self.bdeliver.delivery_tag)

            from coolamqp.objects import ReceivedMessage
            rm = ReceivedMessage(
                b''.join(map(six.binary_type, self.body)), #todo inefficient as FUUUCK
                self.bdeliver.exchange,
                self.bdeliver.routing_key,
                self.header.properties,
                self.bdeliver.delivery_tag,
                None if self.consumer.no_ack else self.confirm(self.bdeliver.delivery_tag, True),
                None if self.consumer.no_ack else self.confirm(self.bdeliver.delivery_tag, False),
            )

            self.consumer.on_message(rm)

            self.state = 0

        # at this point it's safe to clear the body
        self.body = []