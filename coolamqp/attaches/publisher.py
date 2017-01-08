# coding=utf-8
"""
Module used to publish messages.

Expect wild NameErrors if you build this without RabbitMQ extensions (enabled by default),
and try to use MODE_CNPUB.

If you use a broker that doesn't support these, just don't use MODE_CNPUB. CoolAMQP is smart enough
to check with the broker beforehand.
"""
from __future__ import absolute_import, division, print_function
import six
import warnings
import logging
import collections
from coolamqp.framing.definitions import ChannelOpenOk

try:
    # these extensions will be available
    from coolamqp.framing.definitions import ConfirmSelect, ConfirmSelectOk
except ImportError:
    pass

from coolamqp.attaches.channeler import Channeler, ST_ONLINE, ST_OFFLINE
from coolamqp.uplink import PUBLISHER_CONFIRMS


logger = logging.getLogger(__name__)

MODE_NOACK = 0
MODE_CNPUB = 1  # this will be available only if suitable extensions were used


class Publisher(Channeler):
    """
    An object that is capable of sucking into a Connection and sending messages.
    Depending on it's characteristic, it may process messages in:

        - non-ack mode (default) - messages will be dropped on the floor if there is no active uplink
        - Consumer Publish mode - requires broker support, each message will be ACK/NACKed by the broker
                                  messages will survive broker reconnections.

                                  If you support this, it is your job to ensure that broker supports
                                  publisher_confirms. If it doesn't, this publisher will enter ST_OFFLINE
                                  and emit a warning.

        Other modes may be added in the future.
    """

    def __init__(self, mode):
        """
        Create a new publisher
        :param mode: Publishing mode to use. One of:
                         MODE_NOACK - use non-ack mode
                         MODE_CNPUB - use consumer publishing mode. TypeError will be raised when this publisher
                                      if attached to a consumer that doesn't have consumer publishes negotiated
        :type mode: MODE_NOACK or MODE_CNPUB
        :raise ValueError: mode invalid
        """
        super(Publisher, self).__init__()
        if mode not in (MODE_NOACK, MODE_CNPUB):
            raise ValueError(u'Invalid publisher mode')

        self.mode = mode

        self.messages = collections.deque() # Messages to publish. From newest to last.
                                            # tuple of (Message object, exchange name::str, routing_key::str,
                                            #           Future to confirm or None, flags as tuple|empty tuple

        self.delivery_tag = 0       # next delivery tag


    def publish(self, message, exchange_name=b'', routing_key=b''):
        """
        Schedule to have a message published.

        :param message: Message object to send
        :param exchange_name: exchange name to use. Default direct exchange by default
        :param routing_key: routing key to use
        :return: a Future object symbolizing delivering the message to AMQP (or any else guarantees publisher mode
            will make).
            This is None when mode is noack
        """
        # Formulate the request
        if self.mode == MODE_NOACK:

            # If we are not connected right now, drop the message on the floor and log it with DEBUG
            if self.state != ST_ONLINE:
                logger.debug(u'Publish request, but not connected - dropping the message')
            else:
                # Dispatch!
                pass



            self.messages.append((
                message,
                exchange_name,
                routing_key,
                None,
                ()
            ))
        else:
            fut = u'banana banana banana'
            self.messages.append((
                message,
                exchange_name,
                routing_key,
                fut
            ))
            return fut

        # Attempt dispatching messages as possible
        if self.mode == MODE_NOACK:
            pass

    def on_setup(self, payload):

        # Assert that mode is OK
        if self.mode == MODE_CNPUB:
            if PUBLISHER_CONFIRMS not in self.connection.extensions:
                warnings.warn(u'Broker does not support publisher_confirms, refusing to start publisher',
                              RuntimeWarning)
                self.state = ST_OFFLINE
                return

        if isinstance(payload, ChannelOpenOk):
            # Ok, if this has a mode different from MODE_NOACK, we need to additionally set up
            # the functionality.

            if self.mode == MODE_CNPUB:
                self.method_and_watch(ConfirmSelect(False), ConfirmSelectOk, self.on_setup)
            elif self.mode == MODE_NOACK:
                # A-OK! Boot it.
                self.state = ST_ONLINE
                self.on_operational(True)

        elif self.mode == MODE_CNPUB:
            # Because only in this case it makes sense to check for MODE_CNPUB
            if isinstance(payload, ConfirmSelectOk):
                # A-OK! Boot it.
                self.state = ST_ONLINE
                self.on_operational(True)



