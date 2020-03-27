# coding=UTF-8
"""
Core objects used in CoolAMQP
"""
import typing as tp
import logging
import uuid

import six

from coolamqp.framing.definitions import \
    BasicContentPropertyList as MessageProperties
from coolamqp.framing.base import AMQPFrame

logger = logging.getLogger(__name__)

EMPTY_PROPERTIES = MessageProperties()

try:
    Protocol = tp.Protocol
except AttributeError:
    Protocol = object


def toutf8(q):
    if isinstance(q, six.binary_type):
        q = q.decode('utf8')
    return q


def tobytes(q):
    if isinstance(q, six.text_type):
        q = q.encode('utf8')
    return q


class FrameLogger(Protocol):
    def on_frame(self, timestamp,   # type: float
                 frame,             # type: AMQPFrame
                 direction          # type: str
                 ):
        """
        Log a frame

        :param timestamp: timestamp in seconds since Unix Epoch
        :param frame: AMQPFrame to parse
        :param direction: either 'to_client' when this is frame received from the broker, or
            'to_server' if it's a frame that's being sent to the broker
        """


class Callable(object):
    """
    Add a bunch of callables to one list, and just invoke'm.
    INTERNAL USE ONLY
    #todo not thread safe
    """
    __slots__ = ('callables', 'oneshots')

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

    Properties is a highly regularized class - see
    coolamqp.framing.definitions.BasicContentPropertyList
    for a list of possible properties.
    """
    __slots__ = ('body', 'properties')

    Properties = MessageProperties  # an alias for easier use

    def __init__(self, body,    # type: bytes
                 properties=None):
        """
        Create a Message object.

        Please take care with passing empty bodies, as py-amqp has some
        failure on it.

        :param body: stream of octets
        :type body: anything with a buffer interface
        :param properties: AMQP properties to be sent along.
                           default is 'no properties at all'
                           You can pass a dict - it will be passed to
                           MessageProperties,
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


def LAMBDA_NONE():
    pass


class ReceivedMessage(Message):
    """
    A message that was received from the AMQP broker.

    It additionally has an exchange name, routing key used, it's delivery tag,
    and methods for ack() or nack().

    Note that if the consumer that generated this message was no_ack, .ack()
    and .nack() are no-ops.
    """
    __slots__ = ('delivery_tag', 'exchange_name', 'routing_key', 'ack', 'nack')

    def __init__(self, body,         # type: tp.Union[str, bytes, bytearray, tp.List[memoryview]]
                 exchange_name,      # type: memoryview
                 routing_key,        # type: memoryview
                 properties=None,
                 delivery_tag=None,  # type: int
                 ack=None,           # type: tp.Callable[[], None]
                 nack=None           # type: tp.Callable[[], None]
                 ):
        """
        :param body: message body. A stream of octets.
        :type body: str (py2) or bytes (py3) or a list of memoryviews, if
            particular disabled-by-default option is turned on, or a single memoryview
        :param exchange_name: name of exchange this message was submitted to
        :param routing_key: routing key with which this message was sent
        :param properties: a suitable BasicContentPropertyList subinstance.
                           be prepared that value of properties that are
                           strings will be memoryviews
        :param delivery_tag: delivery tag assigned by AMQP broker to confirm
            this message
        :param ack: a callable to call when you want to ack (via basic.ack)
            this message. None if received by the no-ack mechanism
        :param nack: a callable to call when you want to nack
            (via basic.reject) this message. None if received by the no-ack
             mechanism
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
    __slots__ = ('name', 'type', 'durable', 'auto_delete')

    direct = None  # the direct exchange

    def __init__(self, name=u'',    # type: tp.Union[str, bytes]
                 type=b'direct',    # type: tp.Union[str, bytes]
                 durable=True,      # type: bool
                 auto_delete=False  # type: bool
                 ):
        """
        :type name: unicode is preferred, binary type will get decoded to
             unicode with utf8
        """
        self.name = toutf8(name)  # must be unicode
        self.type = tobytes(type)  # must be bytes
        self.durable = durable
        self.auto_delete = auto_delete

        assert isinstance(self.name, six.text_type)
        assert isinstance(self.type, six.binary_type)

    def __repr__(self):  # type: () -> str
        return u'Exchange(%s, %s, %s, %s)' % (
            repr(self.name), repr(self.type), repr(self.durable),
            repr(self.auto_delete))

    def __hash__(self):  # type: () -> int
        return self.name.__hash__()

    def __eq__(self, other):  # type: (Exchange) -> bool
        return (self.name == other.name) and (type(self) == type(other))


Exchange.direct = Exchange()


class Queue(object):
    """
    This object represents a Queue that applications consume from or publish to.
    """
    __slots__ = ('name', 'durable', 'exchange', 'auto_delete', 'exclusive',
                 'anonymous', 'consumer_tag')

    def __init__(self, name=b'',    # type: tp.Union[str, bytes]
                 durable=False,     # type: bool
                 exchange=None,     # type: tp.Optional[Exchange]
                 exclusive=False,   # type: bool
                 auto_delete=False  # type: bool
                 ):
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
        self.name = tobytes(name)  #: public, must be bytes
        # if name is '', this will be filled in with broker-generated name upon declaration
        self.durable = durable
        self.exchange = exchange
        self.auto_delete = auto_delete
        self.exclusive = exclusive

        self.anonymous = len(
            self.name) == 0  # if this queue is anonymous, it must be regenerated upon reconnect

        self.consumer_tag = self.name if not self.anonymous else uuid.uuid4().hex.encode(
            'utf8')  # bytes, consumer tag to use in AMQP comms

        assert isinstance(self.name, six.binary_type)
        assert isinstance(self.consumer_tag, six.binary_type)

    def __eq__(self, other):
        return (self.name == other.name) and (type(self) == type(other))

    def __hash__(self):
        return hash(self.name)


class NodeDefinition(object):
    """
    Definition of a reachable AMQP node.

    This object is hashable.

    >>> a = NodeDefinition(host='192.168.0.1', user='admin', password='password',
    >>>                   virtual_host='vhost')

    or

    >>> a = NodeDefinition('192.168.0.1', 'admin', 'password')

    or

    >>> a = NodeDefinition('amqp://user:password@host/virtual_host')

    or

    >>> a = NodeDefinition('amqp://user:password@host:port/virtual_host', hearbeat=20)

    AMQP connection string may be either bytes or str/unicode


    Additional keyword parameters that can be specified:
        heartbeat - heartbeat interval in seconds
        port - TCP port to use. Default is 5672

    :raise ValueError: invalid parameters
    """

    def __init__(self, *args, **kwargs):
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
        elif len(args) == 1 and isinstance(args[0],
                                           (six.text_type, six.binary_type)):
            connstr = args[0].decode('utf8') if isinstance(args[0],
                                                           six.binary_type) else \
                args[0]
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

    def __str__(self):  # type: () -> str
        return six.text_type(
            'amqp://%s:%s@%s/%s' % (self.host, self.port, self.user, self.virtual_host))
