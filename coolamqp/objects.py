# coding=UTF-8
"""
Core objects used in CoolAMQP
"""
import uuid
import six
import logging
import warnings

from coolamqp.framing.definitions import BasicContentPropertyList as MessageProperties

logger = logging.getLogger(__name__)

EMPTY_PROPERTIES = MessageProperties()


class Callable(object):
    """
    Add a bunch of callables to one list, and just invoke'm.
    INTERNAL USE ONLY
    """

    def __init__(self, oneshots=False):
        """:param oneshots: if True, callables will be called and discarded"""
        self.callables = []
        self.oneshots = oneshots

    def add(self, callable):
        self.callables.append(callable)

    def __call__(self, *args, **kwargs):
        for callable in self.callables:
            callable(*args, **kwargs)
        if self.oneshots:
            self.callables = []


class Message(object):
    """
    An AMQP message. Has a binary body, and some properties.

    Properties is a highly regularized class - see coolamqp.framing.definitions.BasicContentPropertyList
    for a list of possible properties.
    """

    Properties = MessageProperties  # an alias for easier use

    def __init__(self, body, properties=None):
        """
        Create a Message object.

        Please take care with passing empty bodies, as py-amqp has some failure on it.

        :param body: stream of octets
        :type body: anything with a buffer interface
        :param properties: AMQP properties to be sent along.
                           default is 'no properties at all'
                           You can pass a dict - it will be passed to MessageProperties,
                           but it's slow - don't do that.
        :type properties: MessageProperties instance, None or a dict (SLOW!)
        """
        if isinstance(body, six.text_type):
            raise TypeError(u'body cannot be a text type!')

        self.body = body

        if isinstance(properties, dict):
            self.properties = MessageProperties(**properties)
        elif properties is None:
            self.properties = EMPTY_PROPERTIES
        else:
            self.properties = properties


LAMBDA_NONE = lambda: None


class ReceivedMessage(Message):
    """
    A message that was received from the AMQP broker.

    It additionally has an exchange name, routing key used, it's delivery tag,
    and methods for ack() or nack().

    Note that if the consumer that generated this message was no_ack, .ack() and .nack() are no-ops.
    """

    def __init__(self, body, exchange_name, routing_key,
                 properties=None,
                 delivery_tag=None,
                 ack=None,
                 nack=None):
        """
        :param body: message body. A stream of octets.
        :type body: str (py2) or bytes (py3) or a list of memoryviews, if particular disabled-by-default option
                    is turned on.
        :param exchange_name: name of exchange this message was submitted to
        :type exchange_name: memoryview
        :param routing_key: routing key with which this message was sent
        :type routing_key: memoryview
        :param properties: a suitable BasicContentPropertyList subinstance.
                           be prepared that value of properties that are strings will be memoryviews
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

    direct = None  # the direct exchange

    def __init__(self, name=u'', type=b'direct', durable=True, auto_delete=False):
        self.name = name
        if isinstance(type, six.text_type):
            type = type.encode('utf8')
            warnings.warn(u'type should be a binary type')
        self.type = type  # must be bytes
        self.durable = durable
        self.auto_delete = auto_delete

    def __repr__(self):
        return u'Exchange(%s, %s, %s, %s)' % (
        repr(self.name), repr(self.type), repr(self.durable), repr(self.auto_delete))

    def __hash__(self):
        return self.name.__hash__()

    def __eq__(self, other):
        return (self.name == other.name) and (type(self) == type(other))


Exchange.direct = Exchange()


class Queue(object):
    """
    This object represents a Queue that applications consume from or publish to.
    """

    def __init__(self, name=u'', durable=False, exchange=None, exclusive=False, auto_delete=False):
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
        self.name = name.encode('utf8')  #: public, this is of type bytes ALWAYS
        # if name is '', this will be filled in with broker-generated name upon declaration
        self.durable = durable
        self.exchange = exchange
        self.auto_delete = auto_delete
        self.exclusive = exclusive

        self.anonymous = name == ''  # if this queue is anonymous, it must be regenerated upon reconnect

        self.consumer_tag = name if name != '' else uuid.uuid4().hex  # consumer tag to use in AMQP comms

    def __eq__(self, other):
        return (self.name == other.name) and (type(self) == type(other))

    def __hash__(self):
        return hash(self.name)


class NodeDefinition(object):
    """
    Definition of a reachable AMQP node.

    This object is hashable.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a cluster node definition.

            a = NodeDefinition(host='192.168.0.1', user='admin', password='password',
                            virtual_host='vhost')

        or

            a = NodeDefinition('192.168.0.1', 'admin', 'password')
            
        or
        
            a = NodeDefinition('amqp://user:password@host/virtual_host')
        
        or
        
            a = NodeDefinition('amqp://user:password@host:port/virtual_host', hearbeat=20)

        AMQP connection string may be either bytes or str/unicode
        

        Additional keyword parameters that can be specified:
            heartbeat - heartbeat interval in seconds
            port - TCP port to use. Default is 5672
            
        :raise ValueError: invalid parameters
        """

        self.heartbeat = kwargs.pop('heartbeat', None)
        self.port = kwargs.pop('port', 5672)

        if len(kwargs) > 0:
            # Prepare arguments for amqp.connection.Connection
            self.host = kwargs['host']
            self.user = kwargs['user']
            self.password = kwargs['password']
            self.virtual_host = kwargs.get('virtual_host', '/')
        elif len(args) == 3:
            self.host, self.user, self.password = args
            self.virtual_host = '/'
        elif len(args) == 4:
            self.host, self.user, self.password, self.virtual_host = args
        elif len(args) == 1 and isinstance(args[0], (six.text_type, six.binary_type)):

            if isinstance(args[0], six.binary_type):
                connstr = args[0].decode('utf8')
            else:
                connstr = args[0]

            # AMQP connstring
            if not connstr.startswith(u'amqp://'):
                raise ValueError(u'should begin with amqp://')

            connstr = connstr.replace(u'amqp://', u'')
            self.user, connstr = connstr.split(u':', 1)
            self.password, connstr = connstr.split(u'@', 1)
            self.host, self.virtual_host = connstr.split(u'/', 1)

            if len(self.virtual_host) == 0:
                # empty virtual host is /
                self.virtual_host = u'/'

            if u':' in self.host:
                host, port = self.host.split(u':', 1)
                self.port = int(port)
                # else get that port from kwargs
        else:
            raise ValueError(u'What did you exactly pass?')

    @staticmethod
    def from_str(connstr, **kwargs):
        """
        Return a NodeDefinition from an AMQP connection string.

        It should look like:



        :param connstr: a unicode

        :param heartbeat: heartbeat to use

        :return: NodeDefinition instance
        :raise ValueError: invalid string
        """

        return NodeDefinition(host=host, port=5672, user=user, password=passw, virtual_host=virtual_host,
                              heartbeat=kwargs.get('heartbeat', None))

    def __str__(self):
        return six.text_type(
            b'amqp://%s:%s@%s/%s'.encode('utf8') % (self.host, self.port, self.user, self.virtual_host))
