import uuid

class Message(object):
    """AMQP message object"""

    def __init__(self, body, properties={}):
        """
        Create a Message object
        :param body: stream of octets
        :param properties: AMQP properties to be sent along
        """
        self.body = body
        self.properties = properties


class ReceivedMessage(Message):
    """
    Message as received from AMQP system
    """

    def __init__(self, body, cht, connect_id, exchange_name, routing_key, properties={}, delivery_tag=None):
        """

        :param body: message body. A stream of octets.
        :param cht: parent ClusterHandlerThread that emitted this message
        :param connect_id: connection ID. ClusterHandlerThread will check this in order
            not to ack messages that were received from a dead connection
        :param exchange_name: name of exchange this message was submitted to
        :param routing_key: routing key with which this message was sent
        :param properties: dictionary. Headers received from AMQP

        :param delivery_tag: delivery tag assigned by AMQP broker to confirm this message.
            leave None if auto-ack
        """
        Message.__init__(self, body, headers=headers)

        self.cht = cht
        self.connect_id = connect_id
        self.delivery_tag = delivery_tag
        self.exchange_name = exchange_name
        self.routing_key = routing_key

    def nack(self, on_completed=None):
        """
        Negative-acknowledge this message to the broker.
        :param on_completed: callable/0 to call on acknowledged. Callable will be executed in
            ClusterHandlerThread's context.
        """
        self.cht._do_nackmessage(self, on_completed=on_completed)

    def ack(self, on_completed=None):
        """
        Acknowledge this message to the broker.
        :param on_completed: callable/0 to call on acknowledged. Callable will be executed in
            ClusterHandlerThread's context.
        """
        self.cht._do_ackmessage(self, on_completed=on_completed)


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
        Create a queue definition
        :param name: name of the queue.
            Take special care if this is empty. If empty, this will be filled-in by the broker
            upon declaration. If a disconnect happens, and connection to other node is
            reestablished, this name will CHANGE AGAIN, and be reflected in this object.
            This change will be done before CoolAMQP signals reconnection.
        :param durable: Is the queue durable?
        :param exchange: Exchange(s) this queue is bound to. None for no binding.
            This might be a single Exchange object, or an iterable of exchanges.
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

