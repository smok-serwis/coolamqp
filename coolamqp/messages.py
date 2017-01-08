# coding=UTF-8
import uuid
import six


class Message(object):
    """AMQP message object"""

    def __init__(self, body, properties=None):
        """
        Create a Message object.

        Please take care with passing empty bodies, as py-amqp has some failure on it.

        :param body: stream of octets
        :type body: str (py2) or bytes (py3)
        :param properties: AMQP properties to be sent along
        """
        if isinstance(body, six.text_type):
            raise TypeError('body cannot be a text type!')
        self.body = six.binary_type(body)
        self.properties = properties or {}


LAMBDA_NONE = lambda: None

class ReceivedMessage(Message):
    """Message as received from AMQP system"""

    def __init__(self, body, exchange_name, routing_key,
                 properties=None,
                 delivery_tag=None,
                 ack=None,
                 nack=None):
        """
        :param body: message body. A stream of octets.
        :type body: str (py2) or bytes (py3)
        :param cht: parent ClusterHandlerThread that emitted this message
        :param connect_id: connection ID. ClusterHandlerThread will check this in order
            not to ack messages that were received from a dead connection
        :param exchange_name: name of exchange this message was submitted to
        :param routing_key: routing key with which this message was sent
        :param properties: a suitable BasicContentPropertyList subinstance

        :param delivery_tag: delivery tag assigned by AMQP broker to confirm this message
        :param ack: a callable to call when you want to ack (via basic.ack) this message. None if received
             by the no-ack mechanism
        :param nack: a callable to call when you want to nack (via basic.reject) this message. None if received
             by the no-ack mechanism
        """
        Message.__init__(self, body, properties=properties)

        self.delivery_tag = delivery_tag
        self.exchange_name = exchange_name
        self.routing_key = routing_key

        self.ack = ack or LAMBDA_NONE
        self.nack = nack or LAMBDA_NONE


class Exchange(object):
    """
    This represents an Exchange used in AMQP.
    This is hashable.
    """

    direct = None   # the direct exchange

    def __init__(self, name='', type='direct', durable=True, auto_delete=False):
        self.name = name
        self.type = type
        self.durable = durable
        self.auto_delete = auto_delete

    def __hash__(self):
        return self.name.__hash__()

    def __eq__(self, other):
        return self.name == other.name

Exchange.direct = Exchange()


class Queue(object):
    """
    This object represents a Queue that applications consume from or publish to.
    """

    def __init__(self, name='', durable=False, exchange=None, exclusive=False, auto_delete=False):
        """
        Create a queue definition.

        :param name: name of the queue.
            Take special care if this is empty. If empty, this will be filled-in by the broker
            upon declaration. If a disconnect happens, and connection to other node is
            reestablished, this name will CHANGE AGAIN, and be reflected in this object.
            This change will be done before CoolAMQP signals reconnection.
        :param durable: Is the queue durable?
        :param exchange: Exchange for this queue to bind to. None for no binding.
        :param exclusive: Is this queue exclusive?
        :param auto_delete: Is this queue auto_delete ?
        """
        self.name = name
        # if name is '', this will be filled in with broker-generated name upon declaration
        self.durable = durable
        self.exchange = exchange
        self.auto_delete = auto_delete
        self.exclusive = exclusive

        self.anonymous = name == ''  # if this queue is anonymous, it must be regenerated upon reconnect

        self.consumer_tag = name if name != '' else uuid.uuid4().hex    # consumer tag to use in AMQP comms

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
