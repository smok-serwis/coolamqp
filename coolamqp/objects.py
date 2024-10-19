# coding=UTF-8
"""
Core objects used in CoolAMQP
"""
import logging
import threading
import typing as tp
import uuid
import warnings

import six

from coolamqp.framing.definitions import \
    BasicContentPropertyList as MessageProperties
from coolamqp.framing.field_table import get_type_for

logger = logging.getLogger(__name__)

EMPTY_PROPERTIES = MessageProperties()


def argumentify(arguments):
    if arguments is None:
        return None
    args = []
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            if not isinstance(key, six.binary_type):
                key = key.encode('utf-8')
            args.append((key, (value, get_type_for(value))))
    else:
        for key, value in arguments:
            if not isinstance(key, six.binary_type):
                key = key.encode('utf-8')
            args.append((key, (value, get_type_for(value))))

    return args


def toutf8(q):
    if isinstance(q, six.binary_type):
        q = q.decode('utf8')
    return q


def tobytes(q):
    if isinstance(q, six.text_type):
        q = q.encode('utf8')
    return q


class Callable(object):
    """
    Add a bunch of callables to one list, and just invoke'm.
    INTERNAL USE ONLY
    """
    __slots__ = ('callables', 'oneshots', 'lock')

    def __init__(self, oneshots=False):
        """:param oneshots: if True, callables will be called and discarded"""
        self.callables = []
        self.lock = threading.Lock()
        self.oneshots = oneshots

    def add(self, clbl):
        self.callables.append(clbl)

    def __call__(self, *args, **kwargs):
        with self.lock:
            for clbl in self.callables:
                clbl(*args, **kwargs)
            if self.oneshots:
                self.callables = []


class Message(object):
    """
    An AMQP message. Has a binary body, and some properties.

    Properties is a highly regularized class - see
    coolamqp.framing.definitions.BasicContentPropertyList
    for a list of possible properties.

    :param body: stream of octets
    :type body: anything with a buffer interface
    :param properties: AMQP properties to be sent along.
                       default is 'no properties at all'
                       You can pass a dict - it will be passed to
                       MessageProperties,
                       but it's slow - don't do that.
    :type properties: MessageProperties instance, None or a dict (SLOW!)

    """
    __slots__ = ('body', 'properties')

    Properties = MessageProperties  # an alias for easier use

    def __init__(self, body,         # type: bytes
                 properties=None     # type: tp.Optional[MessageProperties]
                 ):
        """
        Create a Message object.

        Please take care with passing empty bodies, as py-amqp has some
        failure on it.
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

    :ivar body: message body. A stream of octets. str (py2) or bytes (py3) or a list of memoryviews, if
                particular option is set during consume, or a single memoryview
    :ivar exchange_name: name of exchange this message was submitted (a memoryview)
    :param routing_key: routing key with which this message was sent (a memoryview)
    :param properties: a suitable BasicContentPropertyList subinstance.
                       be prepared that value of properties that are
                       strings will be memoryviews
    :param delivery_tag: delivery tag assigned by AMQP broker to confirm
        this message
    """
    __slots__ = ('delivery_tag', 'exchange_name', 'routing_key', '_ack', '_nack',
                 'acked')

    def __init__(self, body,  # type: tp.Union[str, bytes, bytearray, tp.List[memoryview]]
                 exchange_name,  # type: memoryview
                 routing_key,  # type: memoryview
                 properties=None,
                 delivery_tag=None,  # type: int
                 ack=None,  # type: tp.Callable[[], None]
                 nack=None  # type: tp.Callable[[], None]
                 ):
        Message.__init__(self, body, properties=properties)

        self.delivery_tag = delivery_tag
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.acked = False
        self._ack = ack or LAMBDA_NONE
        self._nack = nack or LAMBDA_NONE

    def ack(self):
        """
        Acknowledge reception of this message.

        This is a no-op if a Consumer was called with no_ack=True.

        If called after an ack() or nack() was called, this will be a no-op.
        """
        if self.acked:
            return
        self._ack()
        self.acked = True

    def nack(self):
        """
        Negatively acknowledge reception of this message.

        This is a no-op if a Consumer was called with no_ack=True. If no_ack was False,
        the message will be requeued and redelivered by the broker

        If called after an ack() or nack() was called, this will be a no-op.
        """
        if self.acked:
            return
        self._nack()
        self.acked = True


class Exchange(object):
    """
    This represents an Exchange used in AMQP.
    This is hashable.

    :param name: exchange name
    :param arguments: either a list of (bytes, values) or a dict of (str, value) to pass as an extra argument
    """
    __slots__ = ('name', 'type', 'durable', 'auto_delete', 'arguments')

    direct = None  # the direct exchange

    def __init__(self, name=u'',  # type: tp.Union[str, bytes]
                 type=b'direct',  # type: tp.Union[str, bytes]
                 durable=True,  # type: bool
                 auto_delete=False,  # type: bool
                 arguments=None
                 ):
        self.name = toutf8(name)  # must be unicode
        self.type = tobytes(type)  # must be bytes
        self.durable = durable
        self.auto_delete = auto_delete
        self.arguments = argumentify(arguments)

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



class ServerProperties(object):
    """
    An object describing properties of the target server.

    :ivar version: tuple of (major version, minor version)
    :ivar properties: dictionary of properties (key str, value any)
    :ivar mechanisms: a list of strings, supported auth mechanisms
    :ivar locales: locale in use
    """

    __slots__ = ('version', 'properties', 'mechanisms', 'locales')

    def __init__(self, data):
        self.version = data.version_major, data.version_minor
        self.properties = {}
        for prop_name, prop_value in data.server_properties:
            prop_name = toutf8(prop_name)
            prop_value = prop_value[0]
            if isinstance(prop_value, memoryview):
                prop_value = prop_value.tobytes().decode('utf-8')
            elif isinstance(prop_value, list):
                prop_value = [toutf8(prop[0]) for prop in prop_value]
            self.properties[prop_name] = prop_value
        self.mechanisms = data.mechanisms.tobytes().decode('utf-8').split(' ')
        self.locales = data.locales.tobytes().decode('utf-8')

    def __str__(self):
        return '%s %s %s %s' % (self.version, repr(self.properties), self.mechanisms, self.locales)


class Queue(object):
    """
    This object represents a Queue that applications consume from or publish to.
    Create a queue definition.

    :param name: name of the queue. Generates a random uuid.uuid4().hex if not given. Note that this kind of queue
                 will probably require to be declared.
    :param durable: Is the queue durable?
    :param exchange: Exchange for this queue to bind to. None for no binding.
    :param exclusive: Is this queue exclusive?
    :param auto_delete: Is this queue auto_delete ?
    :param arguments: either a list of (bytes, values) or a dict of (str, value) to pass as an extra argument
    :warning PendingDeprecationWarning: if a non-exclusive auto_delete queue is created or some other combinations
        that will be soon unavailable (eg. RabbitMQ 4.0).
    """
    __slots__ = ('name', 'durable', 'exchange', 'auto_delete', 'exclusive',
                 'anonymous', 'consumer_tag', 'arguments')

    def __init__(self, name=b'',  # type: tp.Union[str, bytes]
                 durable=False,  # type: bool
                 exchange=None,  # type: tp.Optional[Exchange]
                 exclusive=False,  # type: bool
                 auto_delete=False,  # type: bool
                 arguments=None     # type: tp.Union[tp.List[bytes, tp.Any], tp.Dict[str, tp.Any]]
                 ):
        if not name:
            name = uuid.uuid4().hex
        self.name = tobytes(name)  #: public, must be bytes
        # if name is '', this will be filled in with broker-generated name upon declaration
        self.durable = durable
        self.exchange = exchange
        self.auto_delete = auto_delete
        self.exclusive = exclusive
        self.arguments = argumentify(arguments)

        if self.auto_delete and self.durable:
            warnings.warn('This will be removed in RabbitMQ 4.0', PendingDeprecationWarning)

        if self.auto_delete and not self.exclusive:
            warnings.warn('This will be removed in RabbitMQ 4.0', PendingDeprecationWarning)

        self.anonymous = not len(
            self.name)  # if this queue is anonymous, it must be regenerated upon reconnect

        self.consumer_tag = self.name if not self.anonymous else uuid.uuid4().hex.encode(
            'utf8')  # bytes, consumer tag to use in AMQP comms

        assert isinstance(self.name, six.binary_type)
        assert isinstance(self.consumer_tag, six.binary_type)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class QueueBind(object):
    """An order to be declared which binds a given queue to an exchange"""

    __slots__ = ('queue', 'exchange', 'routing_key', 'arguments')

    def __init__(self, queue,   # type: tp.Union[Queue, bytes, unicode]
                 exchange,      # type: tp.Union[Exchange, bytes, unicode]
                 routing_key,    # type: tp.Union[bytes, unicode]
                 arguments=None  # type: tp.Optional[tp.List[tuple[bytes, tp.Any]]]
                 ):
        if isinstance(queue, Queue):
            queue = queue.name
        self.queue = tobytes(queue)        # type: bytes
        if isinstance(exchange, Exchange):
            exchange = exchange.name
        self.exchange = tobytes(exchange)   # type: bytes
        self.routing_key = tobytes(routing_key)     # type: bytes
        self.arguments = argumentify(arguments)

    def __eq__(self, other):
        return self.queue == other.queue and self.exchange == other.exchange and self.routing_key == other.routing_key

    def __hash__(self):
        return hash(self.queue) ^ hash(self.exchange) ^ hash(self.routing_key)


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
            connstr = toutf8(args[0])

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
