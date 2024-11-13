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

from coolamqp.argumentify import argumentify, tobytes, toutf8
from coolamqp.framing.definitions import BasicContentPropertyList

logger = logging.getLogger(__name__)


class MessageProperties(BasicContentPropertyList):
    """
    Properties you can attach to your messages. Only these keys are valid!
    """

    def __new__(cls, *args, **kwargs):
        """
        :param content_type: MIME content type
        :type content_type: binary type (max length 255) (AMQP as shortstr)
        :param content_encoding: MIME content encoding
        :type content_encoding: binary type (max length 255) (AMQP as shortstr)
        :param headers: message header field table. You can pass a dictionary here safely.
        :type headers: table. See coolamqp.uplink.framing.field_table (AMQP as table)
        :param delivery_mode: non-persistent (1) or persistent (2)
        :type delivery_mode: int, 8 bit unsigned (AMQP as octet)
        :param priority: message priority, 0 to 9
        :type priority: int, 8 bit unsigned (AMQP as octet)
        :param correlation_id: application correlation identifier
        :type correlation_id: binary type (max length 255) (AMQP as shortstr)
        :param reply_to: address to reply to
        :type reply_to: binary type (max length 255) (AMQP as shortstr)
        :param expiration: message expiration specification (in milliseconds)
        :type expiration: binary type (max length 255) (AMQP as shortstr)
        :param message_id: application message identifier
        :type message_id: binary type (max length 255) (AMQP as shortstr)
        :param timestamp: message timestamp
        :type timestamp: 64 bit signed POSIX timestamp (in seconds) (AMQP as timestamp)
        :param type_: message type name
        :type type_: binary type (max length 255) (AMQP as shortstr)
        :param user_id: creating user id
        :type user_id: binary type (max length 255) (AMQP as shortstr)
        :param app_id: creating application id
        :type app_id: binary type (max length 255) (AMQP as shortstr)
        :param reserved: reserved, must be empty
        :type reserved: binary type (max length 255) (AMQP as shortstr)
        """
        if 'headers' in kwargs:
            if isinstance(kwargs['headers'], dict):
                kwargs['headers'] = argumentify(kwargs['headers'])
        return BasicContentPropertyList.__new__(cls, *args, **kwargs)


EMPTY_PROPERTIES = MessageProperties()


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
    :param properties: AMQP properties to be sent along. default is 'no properties at all'.
                       You can pass a dict - it will be passed to MessageProperties, but it's slow - don't do that.
    :type properties: :class:`coolamqp.objects.MessageProperties` instance
    """
    __slots__ = ('body', 'properties')

    #: an alias for easier use
    Properties = MessageProperties

    def __init__(self, body,
                 properties=None
                 ):
        """
        Create a Message object.

        Please take care with passing empty bodies, as py-amqp has some
        failure on it.

        :param body: bytes
        :param properties: a :class:`~coolamqp.objects.MessageProperties` to send along
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
    :param type: type of the exchange. So far, valid types are 'direct', 'fanout', 'topic' and 'headers'
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

        if self.auto_delete and self.durable:
            warnings.warn('What is your purpose in declaring a durable auto-delete exchange?', UserWarning)

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
        self.mechanisms = toutf8(data.mechanisms).split(' ')
        self.locales = toutf8(data.locales)


class Queue(object):
    """
    This object represents a Queue that applications consume from or publish to.
    Create a queue definition.

    :param name: name of the queue.
        None (default) for autogeneration. Just follow the rules for :ref:`anonymq`.
        If empty string, a UUID name will be generated, and you won't have an anonymous queue anymore.
    :param durable: Is the queue durable?
    :param exchange: Exchange for this queue to bind to. None for no binding.
    :param exclusive: This queue will be deleted when the connection closes
    :param auto_delete: This queue will be deleted when the last consumer unsubscribes
    :param arguments: either a list of (bytes, values) or a dict of (str, value) to pass as an extra argument
    :param routing_key: routing key that will be used to bind to an exchange. Used only when this
                        queue is associated with an exchange. Default value of blank should suffice.
    :param arguments: either a list of (bytes, values) or a dict of (str, value) to pass as an extra argument during
                      declaration
    :param arguments_bind: arguments to pass to binding to a (headers, I suppose exchange)
    :raises ValueError: tried to create a queue that was not durable or auto_delete
    :raises ValueError: tried to create a queue that was not exclusive or auto_delete and not anonymous
    :raises ValueError: tried to create a queue that was anonymous and not auto_delete or durable
    :warns DeprecationWarning: if a non-exclusive auto_delete queue is created or some other combinations
        that will be soon unavailable (eg. RabbitMQ 4.0).
    :warns UserWarning: if you're declaring an auto_delete or exclusive, anonymous queue
    """
    __slots__ = ('name', 'durable', 'exchange', 'auto_delete', 'exclusive',
                 'anonymous', 'consumer_tag', 'arguments', 'routing_key', 'arguments_bind')

    def __init__(self, name=None,  # type: tp.Union[str, bytes, None]
                 durable=False,  # type: bool
                 exchange=None,  # type: tp.Optional[Exchange]
                 exclusive=True,  # type: bool
                 auto_delete=True,  # type: bool
                 arguments=None,     # type: tp.Union[tp.List[bytes, tp.Any], tp.Dict[str, tp.Any]],
                 routing_key=b'',    #: type: tp.Union[str, bytes]
                 arguments_bind=None,
                 ):
        if name is None:
            self.name = None
        else:
            self.name = tobytes(uuid.uuid4().hex if not name else name)

        self.durable = durable
        self.exchange = exchange
        self.routing_key = tobytes(routing_key)
        self.auto_delete = auto_delete
        self.exclusive = exclusive
        self.arguments = argumentify(arguments)
        self.arguments_bind = argumentify(arguments_bind)
        self.anonymous = self.name is None

        if self.auto_delete and self.durable:
            raise ValueError('Cannot create an auto_delete and durable queue')

        if self.anonymous and (not self.auto_delete or self.durable):
            raise ValueError('Zero sense to make a anonymous non-auto-delete or durable queue')

        if not self.anonymous and (self.auto_delete or self.exclusive):
            warnings.warn('This may cause unpredictable behaviour', UserWarning)

        if self.durable and self.anonymous:
            raise ValueError('Cannot declare an anonymous durable queue')

        if self.auto_delete and not self.exclusive and not self.anonymous:
            raise ValueError('Cannot create an auto_delete and durable queue non-anonymous')

        self.consumer_tag = self.name if not self.anonymous else tobytes(uuid.uuid4().hex)

        if not self.exclusive and self.auto_delete:
            warnings.warn('This will be removed in RabbitMQ 4.0', DeprecationWarning)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return 'Queue(%s, %s, %s, %s, %s, %s' % (self.name, self.durable, self.exchange, self.exclusive, self.arguments)


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
        self.arguments = arguments or []

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
        self.host = None
        self.user = None
        self.password = None
        self.virtual_host = '/'

        if len(args) == 3:
            self.host, self.user, self.password = args
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

        if len(kwargs) > 0:
            # Prepare arguments for amqp.connection.Connection
            self.host = kwargs.get('host', self.host)
            self.user = kwargs.get('user', self.user)
            self.port = kwargs.get('port', self.port)
            self.password = kwargs.get('password', self.password)
            self.virtual_host = kwargs.get('virtual_host', self.virtual_host)

    def __str__(self):  # type: () -> str
        return six.text_type(
            'amqp://%s:%s@%s/%s' % (self.host, self.port, self.user, self.virtual_host))
