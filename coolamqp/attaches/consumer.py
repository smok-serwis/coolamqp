# coding=UTF-8
from __future__ import absolute_import, division, print_function

import io
import logging
import typing as tp
import uuid
from concurrent.futures import Future

from coolamqp.attaches.channeler import Channeler, ST_ONLINE, ST_OFFLINE
from coolamqp.exceptions import AMQPError
from coolamqp.framing.definitions import ChannelOpenOk, BasicConsume, \
    BasicConsumeOk, QueueDeclare, QueueDeclareOk, ExchangeDeclare, \
    ExchangeDeclareOk, \
    QueueBind, QueueBindOk, ChannelClose, BasicDeliver, BasicCancel, \
    BasicAck, BasicReject, RESOURCE_LOCKED, BasicCancelOk, BasicQos, BasicQosOk
from coolamqp.framing.frames import AMQPBodyFrame, AMQPHeaderFrame
from coolamqp.objects import Callable
from coolamqp.uplink import HeaderOrBodyWatch, MethodWatch

logger = logging.getLogger(__name__)

EMPTY_MEMORYVIEW = memoryview(b'')  # for empty messages


class BodyReceiveMode(object):
    # ZC - zero copy
    # C - copy (copies every byte once)

    BYTES = 0  # message.body will be a single bytes object
    # this will gather frames as memoryviews, and b''.join() them upon
    # receiving last frame
    # this is C

    MEMORYVIEW = 1  # message.body will be returned as a memoryview object
    # this is ZC for small messages, and C for multi-frame ones
    # think less than 800B, since 2048 is the buffer for socket recv, and an
    # AMQP frame (or many frames!) have to fit there

    LIST_OF_MEMORYVIEW = 2  # message.body will be returned as list of
    # memoryview objects these constitute received pieces. this is always ZC


class Consumer(Channeler):
    """
    This object represents a consumer in the system.

    Consumer may reside on any AMQP broker, this is to be decided by CoolAMQP.
    Consumer, when created, has the state of ST_SYNCING. CoolAMQP will
    try to declare the consumer where it makes most sense for it to be.

    If it succeeds, the consumer will enter state ST_ONLINE, and callables
    on_start will be called. This means that broker has confirmed that this
    consumer is operational and receiving messages.

    Note that does not attempt to cancel consumers, or any of such nonsense.
    Having a channel per consumer gives you the unique possibility of simply
    closing  the channel. Since this implies cancelling the consumer, here you
    go.

    WARNING: READ DEFAULT VALUES IN CONSTRUCTOR! TAKE CARE WHAT YOUR CONSUMERS
     DO!

    You can subscribe to be informed when the consumer is cancelled (for any
    reason, server or client side) with:

    >>> con, fut = Cluster.consume(...)
    >>> def im_called_on_cancel_for_any_reason():   # must have arity of 0
    >>>     ..
    >>> con.on_cancel.add(im_called_on_cancel_for_any_reason)
    >>> con.cancel()

    Or, if RabbitMQ is in use, you can be informed upon a Consumer Cancel
    Notification:

    >>> con.on_broker_cancel.add(im_cancelled_by_broker)

    :param queue: Queue object, being consumed from right now.
        Note that name of anonymous queue might change at any time!
    :type queue: coolamqp.objects.Queue
    :param on_message: callable that will process incoming messages
    :type on_message: callable(ReceivedMessage instance)
    :param no_ack: Will this consumer require acknowledges from messages?
    :type no_ack: bool
    :param qos: a tuple of (prefetch size, prefetch window) for this
        consumer, or an int (prefetch window only).
        If an int is passed, prefetch size will be set to 0 (which means
        undefined), and this int will be used for prefetch window
    :type qos: tuple(int, int) or tuple(None, int) or int
    :param cancel_on_failure: Consumer will cancel itself when link goes
        down
    :type cancel_on_failure: bool
    :param future_to_notify: Future to succeed when this consumer goes
                             online for the first time.
                             This future can also raise with AMQPError if
                             it fails to.
    :type future_to_notify: concurrent.futures.Future
    :param fail_on_first_time_resource_locked: When consumer is declared
        for the first time, and RESOURCE_LOCKED is encountered, it will
        fail the future with ResourceLocked, and consumer will cancel
        itself.
        By default it will retry until success is made.
        If the consumer doesn't get the chance to be declared - because
        of a connection fail - next reconnect will consider this to be
        SECOND declaration, ie. it will retry ad infinitum
    :type fail_on_first_time_resource_locked: bool
    :param body_receive_mode: how should message.body be received. This
        has a performance impact
    :type body_receive_mode: a property of BodyReceiveMode
    """
    __slots__ = ('queue', 'no_ack', 'on_message', 'cancelled', 'receiver',
                 'attache_group', 'channel_close_sent', 'qos', 'qos_update_sent',
                 'future_to_notify', 'future_to_notify_on_dead',
                 'fail_on_first_time_resource_locked', 'cancel_on_failure',
                 'body_receive_mode', 'consumer_tag', 'on_cancel', 'on_broker_cancel',
                 'hb_watch', 'deliver_watch')

    def __init__(self, queue, on_message, no_ack=True, qos=None,
                 cancel_on_failure=False,
                 future_to_notify=None,
                 fail_on_first_time_resource_locked=False,
                 body_receive_mode=BodyReceiveMode.BYTES
                 ):
        """
        Note that if you specify QoS, it is applied before basic.consume is
        sent. This will prevent the broker from hammering you into oblivion
        with a mountain of messages.
        """
        super(Consumer, self).__init__()

        self.queue = queue
        self.no_ack = no_ack

        self.on_message = on_message

        # consumer?
        self.receiver = None  # MessageReceiver instance

        self.attache_group = None  # attache group this belongs to.
        self.channel_close_sent = False  # for avoiding situations where ChannelClose is sent twice
        # if this is not None, then it has an attribute
        # on_cancel_customer(Consumer instance)
        self.qos = _qosify(qos)
        self.qos_update_sent = False  # QoS was not sent to server

        self.future_to_notify = future_to_notify
        self.future_to_notify_on_dead = None  # .cancel

        self.fail_on_first_time_resource_locked = fail_on_first_time_resource_locked
        self.cancel_on_failure = cancel_on_failure
        self.body_receive_mode = body_receive_mode

        self.consumer_tag = None

        self.on_cancel = Callable(
            oneshots=True)  #: public, called on cancel for any reason
        self.on_broker_cancel = Callable(
            oneshots=True)  #: public, called on Customer Cancel Notification
        #  (RabbitMQ)

    def set_qos(self, prefetch_size, prefetch_count):  # type: (int, int) -> None
        """
        Set new QoS for this consumer.

        :param prefetch_size: prefetch in octets
        :param prefetch_count: prefetch in whole messages
        """
        if self.state == ST_ONLINE:
            self.method(BasicQos(prefetch_size or 0, prefetch_count, False))
        self.qos = prefetch_size or 0, prefetch_count

    def cancel(self):  # type: () -> None
        """
        Cancel the customer.

        .ack() or .nack() for messages from this customer will have no effect.

        :return: a Future to tell when it's done. The future will always
                 succeed - sooner, or later.
                 NOTE: Future is OK'd when entire channel is destroyed
        """

        if self.future_to_notify_on_dead is not None:
            # we cancelled it earlier
            return self.future_to_notify_on_dead
        else:
            self.future_to_notify_on_dead = Future()
            self.future_to_notify_on_dead.set_running_or_notify_cancel()

        self.cancelled = True
        self.on_cancel()
        # you'll blow up big next time you try to use this consumer if you
        # can't cancel, but just close
        if self.consumer_tag is not None:
            if not self.channel_close_sent and self.state == ST_ONLINE:
                self.method_and_watch(BasicCancel(self.consumer_tag, False),
                                      [BasicCancelOk],
                                      self.on_close)
        else:
            if not self.channel_close_sent and self.state == ST_ONLINE:
                self.method(ChannelClose(0, b'cancelling', 0, 0))
                self.channel_close_sent = True

        if self.attache_group is not None:
            self.attache_group.on_cancel_customer(self)

        return self.future_to_notify_on_dead

    def on_operational(self, operational):  # type: (bool) -> None
        super(Consumer, self).on_operational(operational)

        if operational:
            self.channel_close_sent = False
            self.receiver = MessageReceiver(self)

            # notify the future
            if self.future_to_notify is not None:
                self.future_to_notify.set_result(None)
                self.future_to_notify = None

        else:
            self.hb_watch.cancel()
            self.deliver_watch.cancel()
            self.receiver.on_gone()
            self.receiver = None

    def on_close(self, payload=None):
        # type: (tp.Optional[coolamqp.framing.base.AMQPMethodPayload]) -> None
        """
        Handle closing the channel. It sounds like an exception...

        This is done in two steps:
        1. self.state <- ST_OFFLINE, on_event(EV_OFFLINE)   upon detecting
           that no more messages will
           be there
        2. self.channel_id <- None, channel is returned to Connection - c
           hannel has been physically torn down

        Note, this can be called multiple times, and eventually with None.

        """
        if self.cancel_on_failure and (not self.cancelled):
            logger.debug(
                'Consumer is cancel_on_failure and failure seen, True->cancelled')
            self.cancelled = True
            self.on_cancel()

        if self.state == ST_ONLINE:
            # The channel has just lost operationality!
            self.on_operational(False)
            self.state = ST_OFFLINE

            # deliver and head/body watch will clean up after themselves

        should_retry = False

        if isinstance(payload, BasicCancel):
            # Consumer Cancel Notification - by RabbitMQ
            # send them back those memoryviews :D

            # on_close is a one_shot watch. We need to re-register it now.
            self.register_on_close_watch()
            if not self.channel_close_sent:
                self.methods([BasicCancelOk(payload.consumer_tag),
                              ChannelClose(0, b'Received basic.cancel', 0, 0)])
                self.channel_close_sent = True
            self.cancelled = True  # wasn't I?
            self.on_cancel()
            self.on_broker_cancel()
            return

        if isinstance(payload, BasicCancelOk):
            # OK, our cancelling went just fine - proceed with teardown
            self.register_on_close_watch()
            if not self.channel_close_sent:
                self.method(ChannelClose(0, b'Received basic.cancel-ok', 0, 0))
                self.channel_close_sent = True
            return

        if isinstance(payload, ChannelClose):
            rc = payload.reply_code
            if rc == RESOURCE_LOCKED:
                # special handling
                # This is because we might be reconnecting, and the broker
                # doesn't know yet that we are dead.
                # it won't release our exclusive channels, and that's why
                # we'll get RESOURCE_LOCKED.

                if self.fail_on_first_time_resource_locked:
                    # still, a RESOURCE_LOCKED on a first declaration ever
                    # suggests something is very wrong
                    self.cancelled = True
                    self.on_cancel()
                else:
                    # Do not notify the user, and retry at will.
                    # Do not zero the future - we will need to later confirm
                    # it, so it doesn't leak.
                    should_retry = True

            if self.future_to_notify:
                self.future_to_notify.set_exception(AMQPError(payload))
                self.future_to_notify = None
                logger.debug('Notifying connection closed with %s', payload)

        # We might not want to throw the connection away.
        should_retry = should_retry and (not self.cancelled)

        old_con = self.connection

        super(Consumer, self).on_close(
            payload)  # this None's self.connection and returns port
        self.fail_on_first_time_resource_locked = False

        if self.future_to_notify_on_dead:  # notify it was cancelled
            logger.info('Consumer successfully cancelled')
            self.future_to_notify_on_dead.set_result(None)
            self.future_to_notify_on_dead = None
        if should_retry:
            if old_con.state == ST_ONLINE:
                logger.info('Retrying with %s', self.queue.name)
                self.attach(old_con)

    def on_delivery(self, sth):
        """
        Callback for delivery-related shit

        :param sth: AMQPMethodFrame WITH basic-deliver, AMQPHeaderFrame or
            AMQPBodyFrame
        """

        if self.receiver is None:
            # dead, cancelled, whatever
            return

        if isinstance(sth, BasicDeliver):
            self.receiver.on_basic_deliver(sth)
        elif isinstance(sth, AMQPBodyFrame):
            self.receiver.on_body(sth.data)
        elif isinstance(sth, AMQPHeaderFrame):
            self.receiver.on_head(sth)

            # No point in listening for more stuff, that's all the watches
            # even listen for

    def on_setup(self, payload):  # type: (coolamqp.framing.base.AMQPMethodPayload) -> None
        """Called with different kinds of frames - during setup"""

        if isinstance(payload, ChannelOpenOk):
            # Do we need to declare the exchange?

            if self.queue.exchange is not None:
                self.connection.method_and_watch(
                    self.channel_id,
                    ExchangeDeclare(self.queue.exchange.name.encode('utf8'),
                                    self.queue.exchange.type,
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

            name = b'' if self.queue.anonymous else self.queue.name

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
                self.queue.name = payload.queue.tobytes()

            # We need any form of binding.
            if self.queue.exchange is not None:
                self.method_and_watch(
                    QueueBind(
                        self.queue.name,
                        self.queue.exchange.name.encode('utf8'),
                        b'', False, []),
                    QueueBindOk,
                    self.on_setup
                )
            else:
                # default exchange, pretend it was bind ok
                self.on_setup(QueueBindOk())
        elif isinstance(payload, QueueBindOk):
            if self.qos is not None:
                self.method_and_watch(
                    BasicQos(self.qos[0], self.qos[1], False),
                    BasicQosOk,
                    self.on_setup
                )
            else:
                self.on_setup(BasicQosOk())  # pretend QoS went ok
        elif isinstance(payload, BasicQosOk):
            self.consumer_tag = uuid.uuid4().hex.encode(
                'utf8')  # str in py2, unicode in py3
            self.method_and_watch(
                BasicConsume(self.queue.name, self.consumer_tag,
                             False, self.no_ack, self.queue.exclusive, False,
                             []),
                BasicConsumeOk,
                self.on_setup
            )
        elif isinstance(payload, BasicConsumeOk):
            # AWWW RIGHT~!!! We're good.
            self.on_operational(True)
            consumer_tag = self.consumer_tag

            # Register watches for receiving shit
            # this is multi-shot by default
            self.hb_watch = HeaderOrBodyWatch(self.channel_id,
                                              self.on_delivery)
            self.connection.watch(self.hb_watch)

            # multi-shot watches need manual cleanup!
            self.deliver_watch = MethodWatch(self.channel_id, BasicDeliver,
                                             self.on_delivery)
            self.deliver_watch.oneshot = False
            self.connection.watch(self.deliver_watch)

            self.state = ST_ONLINE

            if self.cancelled:
                self.method(ChannelClose(0, b'Received basic.cancel-ok', 0, 0))
                self.channel_close_sent = True
                self.state = ST_OFFLINE
                return

            # resend QoS, in case of sth
            if self.qos is not None:
                self.set_qos(self.qos[0], self.qos[1])


def _qosify(qos):
    if qos is not None:
        if isinstance(qos, int):
            qos = 0, qos
        elif qos[0] is None:
            qos = 0, qos[1]  # prefetch_size=0=undefined
    return qos


class MessageReceiver(object):
    """This is an object that is used to received messages.

    It maintains all the state, and is used to ack/nack messages as well.

    This object is TORN DOWN when a consumer goes offline,
    and is recreated when it goes online.

    This is called by consumer upon receiving different parts of the message,
    and may opt to kill the connection on bad framing with
    self.consumer.connection.send(None)
    """
    __slots__ = ('consumer', 'state', 'bdeliver', 'header', 'body', 'data_to_go',
                 'message_size', 'offset', 'acks_pending', 'recv_mode')

    def __init__(self, consumer):  # type: (Consumer) -> None
        self.consumer = consumer
        self.state = 0  # 0 - waiting for Basic-Deliver
        # 1 - waiting for Header
        # 2 - waiting for Body [all]
        # 3 - gone!

        self.bdeliver = None  # payload of Basic-Deliver
        self.header = None  # AMQPHeaderFrame
        if consumer.body_receive_mode == BodyReceiveMode.MEMORYVIEW:
            self.body = None  # None is an important sign - first piece of
            # message
        else:
            self.body = []  # list of payloads
        self.data_to_go = None  # set on receiving header, how much bytes we
        # need yet
        self.message_size = None  # in bytes, of currently received message
        self.offset = 0  # used only in MEMORYVIEW mode - pointer to self.body
        #  (which would be a buffer)

        self.acks_pending = set()  # list of things to ack/reject

        self.recv_mode = consumer.body_receive_mode
        # if BYTES, pieces (as mvs) are received into .body and b''.join()ed
        #     at the end
        # if MEMORYVIEW:
        #                   upon first piece, if it's a single-frame message,
        #                        it's returned at once
        #                   if multiframe, self.body is made into a buffer
        #                        and further are received into it
        # if LIST_OF_MEMORYVIEW, pieces (as mvs) are stored into .body, and
        #     that's returned

    def on_gone(self):
        """Called by Consumer to inform upon discarding this receiver"""
        self.state = 3

    def confirm(self, delivery_tag, success):  # type: (int, tp.Callable[[], None]) -> None
        """
        This crafts a constructor for confirming messages.

        This should return a callable/0, whose calling will ACK or REJECT the
        message.
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
                return  # cancelled!

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
        self.message_size = self.data_to_go = frame.body_size
        self.state = 2

        if self.header.body_size == 0:
            # An empty message is no common guest. It won't have a BODY field
            #  though...
            self.on_body(EMPTY_MEMORYVIEW)  # trigger it manually

    def on_basic_deliver(self, payload):
        assert self.state == 0
        self.bdeliver = payload
        self.state = 1

    def on_body(self, payload):
        """:type payload: buffer"""
        assert self.state == 2
        self.data_to_go -= len(payload)

        if self.recv_mode == BodyReceiveMode.MEMORYVIEW:

            if self.body is not None:
                # continuing a multipart
                self.body[self.offset:self.offset + len(payload)] = payload
                self.offset += len(payload)
            else:
                # new one
                if self.data_to_go == 0:  # special case - single frame message
                    self.body = payload
                else:
                    self.body = memoryview(bytearray(self.message_size))
                    self.body[0:len(payload)] = payload
                    self.offset = len(payload)

        else:  # BYTES and LIST_OF_MEMORYVIEW
            self.body.append(payload)

        assert self.data_to_go >= 0

        if self.data_to_go == 0:
            ack_expected = not self.consumer.no_ack

            # Message A-OK!

            if ack_expected:
                self.acks_pending.add(self.bdeliver.delivery_tag)

            from coolamqp.objects import ReceivedMessage

            # Does body need preprocessing?
            body = self.body
            if self.recv_mode == BodyReceiveMode.BYTES:
                if len(self.body) == 1:
                    # common case :)
                    body = self.body[0].tobytes()
                else:
                    # since b''.join() with list comprehension and .tobytes()
                    #  would create
                    # an extra copy of string
                    bio = io.BytesIO()
                    for mv in body:
                        bio.write(mv)

                    body = bio.getvalue()
            # if MEMORYVIEW, then it's already ok

            rm = ReceivedMessage(
                body,
                self.bdeliver.exchange,
                self.bdeliver.routing_key,
                self.header.properties,
                self.bdeliver.delivery_tag,
                None if self.consumer.no_ack else self.confirm(
                    self.bdeliver.delivery_tag, True),
                None if self.consumer.no_ack else self.confirm(
                    self.bdeliver.delivery_tag, False),
            )

            self.consumer.on_message(rm)

            self.state = 0

            # at this point it's safe to clear the body
            if self.recv_mode == BodyReceiveMode.MEMORYVIEW:
                self.body = None
            else:
                self.body = []
