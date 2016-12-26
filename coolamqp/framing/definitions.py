# coding=UTF-8
from __future__ import print_function, absolute_import
"""
Constants used in AMQP protocol.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See utils/compdefs.py for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016 DMS Serwis s.c.
"""

# Core frame types
FRAME_METHOD = 1
FRAME_HEADER = 2
FRAME_BODY = 3
FRAME_HEARTBEAT = 8
FRAME_MIN_SIZE = 4096
FRAME_END = 206
REPLY_SUCCESS = 200 # Indicates that the method completed successfully. This reply code is
                    # reserved for future use - the current protocol design does not use positive
                    # confirmation and reply codes are sent only in case of an error.
CONTENT_TOO_LARGE = 311 # The client attempted to transfer content larger than the server could accept
                        # at the present time. The client may retry at a later time.
NO_CONSUMERS = 313 # When the exchange cannot deliver to a consumer when the immediate flag is
                   # set. As a result of pending data on the queue or the absence of any
                   # consumers of the queue.
CONNECTION_FORCED = 320 # An operator intervened to close the connection for some reason. The client
                        # may retry at some later date.
INVALID_PATH = 402 # The client tried to work with an unknown virtual host.
ACCESS_REFUSED = 403 # The client attempted to work with a server entity to which it has no
                     # access due to security settings.
NOT_FOUND = 404 # The client attempted to work with a server entity that does not exist.
RESOURCE_LOCKED = 405 # The client attempted to work with a server entity to which it has no
                      # access because another client is working with it.
PRECONDITION_FAILED = 406 # The client requested a method that was not allowed because some precondition
                          # failed.
FRAME_ERROR = 501 # The sender sent a malformed frame that the recipient could not decode.
                  # This strongly implies a programming error in the sending peer.
SYNTAX_ERROR = 502 # The sender sent a frame that contained illegal values for one or more
                   # fields. This strongly implies a programming error in the sending peer.
COMMAND_INVALID = 503 # The client sent an invalid sequence of frames, attempting to perform an
                      # operation that was considered invalid by the server. This usually implies
                      # a programming error in the client.
CHANNEL_ERROR = 504 # The client attempted to work with a channel that had not been correctly
                    # opened. This most likely indicates a fault in the client layer.
UNEXPECTED_FRAME = 505 # The peer sent a frame that was not expected, usually in the context of
                       # a content header and body.  This strongly indicates a fault in the peer's
                       # content processing.
RESOURCE_ERROR = 506 # The server could not complete the method because it lacked sufficient
                     # resources. This may be due to the client creating too many of some type
                     # of entity.
NOT_ALLOWED = 530 # The client tried to work with some entity in a manner that is prohibited
                  # by the server, due to security settings or by some other criteria.
NOT_IMPLEMENTED = 540 # The client tried to use functionality that is not implemented in the
                      # server.
INTERNAL_ERROR = 541 # The server could not complete the method because of an internal error.
                     # The server may require intervention by an operator in order to resume
                     # normal operations.
DOMAIN_TO_BASIC_TYPE = {
    u'class-id': u'short',
    u'consumer-tag': u'shortstr',
    u'delivery-tag': u'longlong',
    u'exchange-name': u'shortstr',
    u'method-id': u'short',
    u'no-ack': u'bit',
    u'no-local': u'bit',
    u'no-wait': u'bit',
    u'path': u'shortstr',
    u'peer-properties': u'table',
    u'queue-name': u'shortstr',
    u'redelivered': u'bit',
    u'message-count': u'long',
    u'reply-code': u'short',
    u'reply-text': u'shortstr',
    u'bit': None,
    u'octet': None,
    u'short': None,
    u'long': None,
    u'longlong': None,
    u'shortstr': None,
    u'longstr': None,
    u'timestamp': None,
    u'table': None,
}


class AMQPClass(object):
    pass


class AMQPMethod(object):
    RESPONSE_TO = None
    REPLY_WITH = []


class Connection(AMQPClass):
    """
    The connection class provides methods for a client to establish a network connection to
    
    a server, and for both peers to operate the connection thereafter.
    """
    NAME = u'connection'
    INDEX = 10


class ConnectionClose(AMQPMethod):
    """
    Request a connection close
    
    This method indicates that the sender wants to close the connection. This may be
    due to internal conditions (e.g. a forced shut-down) or due to an error handling
    a specific method, i.e. an exception. When a close is due to an exception, the
    sender provides the class and method id of the method which caused the exception.
    """
    CLASS = Connection
    NAME = u'close'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 50
    FULLNAME = u'connection.close'
    SYNCHRONOUS = True
    REPLY_WITH = [ConnectionCloseOk]
    FIELDS = [
        (u'reply-code', u'reply-code', u'short'), 
        (u'reply-text', u'reply-text', u'shortstr'), 
        (u'class-id', u'class-id', u'short'),  # failing method class
        (u'method-id', u'method-id', u'short'),  # failing method ID
    ]

    def __init__(self, reply_code, reply_text, class_id, method_id):
        """
        Create frame connection.close

        :type reply_code: reply-code (as short)
        :type reply_text: reply-text (as shortstr)
        :param class_id: Failing method class
            When the close is provoked by a method exception, this is the class of the
            method.
        :type class_id: class-id (as short)
        :param method_id: Failing method id
            When the close is provoked by a method exception, this is the ID of the method.
        :type method_id: method-id (as short)
        """
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.class_id = class_id
        self.method_id = method_id

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionCloseOk(AMQPMethod):
    """
    Confirm a connection close
    
    This method confirms a Connection.Close method and tells the recipient that it is
    safe to release resources for the connection and close the socket.
    """
    CLASS = Connection
    NAME = u'close-ok'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 51
    FULLNAME = u'connection.close-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ConnectionClose
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame connection.close-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionOpen(AMQPMethod):
    """
    Open connection to virtual host
    
    This method opens a connection to a virtual host, which is a collection of
    resources, and acts to separate multiple application domains within a server.
    The server may apply arbitrary limits per virtual host, such as the number
    of each type of entity that may be used, per connection and/or in total.
    """
    CLASS = Connection
    NAME = u'open'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 40
    FULLNAME = u'connection.open'
    SYNCHRONOUS = True
    REPLY_WITH = [ConnectionOpenOk]
    FIELDS = [
        (u'virtual-host', u'path', u'shortstr'),  # virtual host name
        (u'reserved-1', u'shortstr', u'shortstr'), 
        (u'reserved-2', u'bit', u'bit'), 
    ]

    def __init__(self, virtual_host):
        """
        Create frame connection.open

        :param virtual_host: Virtual host name
            The name of the virtual host to work with.
        :type virtual_host: path (as shortstr)
        """
        self.virtual_host = virtual_host

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionOpenOk(AMQPMethod):
    """
    Signal that connection is ready
    
    This method signals to the client that the connection is ready for use.
    """
    CLASS = Connection
    NAME = u'open-ok'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 41
    FULLNAME = u'connection.open-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ConnectionOpen
    FIELDS = [
        (u'reserved-1', u'shortstr', u'shortstr'), 
    ]

    def __init__(self):
        """
        Create frame connection.open-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionStart(AMQPMethod):
    """
    Start connection negotiation
    
    This method starts the connection negotiation process by telling the client the
    protocol version that the server proposes, along with a list of security mechanisms
    which the client can use for authentication.
    """
    CLASS = Connection
    NAME = u'start'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 10
    FULLNAME = u'connection.start'
    SYNCHRONOUS = True
    REPLY_WITH = [ConnectionStartOk]
    FIELDS = [
        (u'version-major', u'octet', u'octet'),  # protocol major version
        (u'version-minor', u'octet', u'octet'),  # protocol minor version
        (u'server-properties', u'peer-properties', u'table'),  # server properties
        (u'mechanisms', u'longstr', u'longstr'),  # available security mechanisms
        (u'locales', u'longstr', u'longstr'),  # available message locales
    ]

    def __init__(self, version_major, version_minor, server_properties, mechanisms, locales):
        """
        Create frame connection.start

        :param version_major: Protocol major version
            The major version number can take any value from 0 to 99 as defined in the
            AMQP specification.
        :type version_major: octet (as octet)
        :param version_minor: Protocol minor version
            The minor version number can take any value from 0 to 99 as defined in the
            AMQP specification.
        :type version_minor: octet (as octet)
        :param server_properties: Server properties
            The properties SHOULD contain at least these fields: "host", specifying the
            server host name or address, "product", giving the name of the server product,
            "version", giving the name of the server version, "platform", giving the name
            of the operating system, "copyright", if appropriate, and "information", giving
            other general information.
        :type server_properties: peer-properties (as table)
        :param mechanisms: Available security mechanisms
            A list of the security mechanisms that the server supports, delimited by spaces.
        :type mechanisms: longstr (as longstr)
        :param locales: Available message locales
            A list of the message locales that the server supports, delimited by spaces. The
            locale defines the language in which the server will send reply texts.
        :type locales: longstr (as longstr)
        """
        self.version_major = version_major
        self.version_minor = version_minor
        self.server_properties = server_properties
        self.mechanisms = mechanisms
        self.locales = locales

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionSecure(AMQPMethod):
    """
    Security mechanism challenge
    
    The SASL protocol works by exchanging challenges and responses until both peers have
    received sufficient information to authenticate each other. This method challenges
    the client to provide more information.
    """
    CLASS = Connection
    NAME = u'secure'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 20
    FULLNAME = u'connection.secure'
    SYNCHRONOUS = True
    REPLY_WITH = [ConnectionSecureOk]
    FIELDS = [
        (u'challenge', u'longstr', u'longstr'),  # security challenge data
    ]

    def __init__(self, challenge):
        """
        Create frame connection.secure

        :param challenge: Security challenge data
            Challenge information, a block of opaque binary data passed to the security
            mechanism.
        :type challenge: longstr (as longstr)
        """
        self.challenge = challenge

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionStartOk(AMQPMethod):
    """
    Select security mechanism and locale
    
    This method selects a SASL security mechanism.
    """
    CLASS = Connection
    NAME = u'start-ok'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 11
    FULLNAME = u'connection.start-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ConnectionStart
    FIELDS = [
        (u'client-properties', u'peer-properties', u'table'),  # client properties
        (u'mechanism', u'shortstr', u'shortstr'),  # selected security mechanism
        (u'response', u'longstr', u'longstr'),  # security response data
        (u'locale', u'shortstr', u'shortstr'),  # selected message locale
    ]

    def __init__(self, client_properties, mechanism, response, locale):
        """
        Create frame connection.start-ok

        :param client_properties: Client properties
            The properties SHOULD contain at least these fields: "product", giving the name
            of the client product, "version", giving the name of the client version, "platform",
            giving the name of the operating system, "copyright", if appropriate, and
            "information", giving other general information.
        :type client_properties: peer-properties (as table)
        :param mechanism: Selected security mechanism
            A single security mechanisms selected by the client, which must be one of those
            specified by the server.
        :type mechanism: shortstr (as shortstr)
        :param response: Security response data
            A block of opaque data passed to the security mechanism. The contents of this
            data are defined by the SASL security mechanism.
        :type response: longstr (as longstr)
        :param locale: Selected message locale
            A single message locale selected by the client, which must be one of those
            specified by the server.
        :type locale: shortstr (as shortstr)
        """
        self.client_properties = client_properties
        self.mechanism = mechanism
        self.response = response
        self.locale = locale

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionSecureOk(AMQPMethod):
    """
    Security mechanism response
    
    This method attempts to authenticate, passing a block of SASL data for the security
    mechanism at the server side.
    """
    CLASS = Connection
    NAME = u'secure-ok'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 21
    FULLNAME = u'connection.secure-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ConnectionSecure
    FIELDS = [
        (u'response', u'longstr', u'longstr'),  # security response data
    ]

    def __init__(self, response):
        """
        Create frame connection.secure-ok

        :param response: Security response data
            A block of opaque data passed to the security mechanism. The contents of this
            data are defined by the SASL security mechanism.
        :type response: longstr (as longstr)
        """
        self.response = response

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionTune(AMQPMethod):
    """
    Propose connection tuning parameters
    
    This method proposes a set of connection configuration values to the client. The
    client can accept and/or adjust these.
    """
    CLASS = Connection
    NAME = u'tune'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 30
    FULLNAME = u'connection.tune'
    SYNCHRONOUS = True
    REPLY_WITH = [ConnectionTuneOk]
    FIELDS = [
        (u'channel-max', u'short', u'short'),  # proposed maximum channels
        (u'frame-max', u'long', u'long'),  # proposed maximum frame size
        (u'heartbeat', u'short', u'short'),  # desired heartbeat delay
    ]

    def __init__(self, channel_max, frame_max, heartbeat):
        """
        Create frame connection.tune

        :param channel_max: Proposed maximum channels
            Specifies highest channel number that the server permits.  Usable channel numbers
            are in the range 1..channel-max.  Zero indicates no specified limit.
        :type channel_max: short (as short)
        :param frame_max: Proposed maximum frame size
            The largest frame size that the server proposes for the connection, including
            frame header and end-byte.  The client can negotiate a lower value. Zero means
            that the server does not impose any specific limit but may reject very large
            frames if it cannot allocate resources for them.
        :type frame_max: long (as long)
        :param heartbeat: Desired heartbeat delay
            The delay, in seconds, of the connection heartbeat that the server wants.
            Zero means the server does not want a heartbeat.
        :type heartbeat: short (as short)
        """
        self.channel_max = channel_max
        self.frame_max = frame_max
        self.heartbeat = heartbeat

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ConnectionTuneOk(AMQPMethod):
    """
    Negotiate connection tuning parameters
    
    This method sends the client's connection tuning parameters to the server.
    Certain fields are negotiated, others provide capability information.
    """
    CLASS = Connection
    NAME = u'tune-ok'
    CLASSNAME = u'connection'
    CLASS_INDEX = 10
    METHOD_INDEX = 31
    FULLNAME = u'connection.tune-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ConnectionTune
    FIELDS = [
        (u'channel-max', u'short', u'short'),  # negotiated maximum channels
        (u'frame-max', u'long', u'long'),  # negotiated maximum frame size
        (u'heartbeat', u'short', u'short'),  # desired heartbeat delay
    ]

    def __init__(self, channel_max, frame_max, heartbeat):
        """
        Create frame connection.tune-ok

        :param channel_max: Negotiated maximum channels
            The maximum total number of channels that the client will use per connection.
        :type channel_max: short (as short)
        :param frame_max: Negotiated maximum frame size
            The largest frame size that the client and server will use for the connection.
            Zero means that the client does not impose any specific limit but may reject
            very large frames if it cannot allocate resources for them. Note that the
            frame-max limit applies principally to content frames, where large contents can
            be broken into frames of arbitrary size.
        :type frame_max: long (as long)
        :param heartbeat: Desired heartbeat delay
            The delay, in seconds, of the connection heartbeat that the client wants. Zero
            means the client does not want a heartbeat.
        :type heartbeat: short (as short)
        """
        self.channel_max = channel_max
        self.frame_max = frame_max
        self.heartbeat = heartbeat

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()

class Channel(AMQPClass):
    """
    The channel class provides methods for a client to establish a channel to a
    
    server and for both peers to operate the channel thereafter.
    """
    NAME = u'channel'
    INDEX = 20


class ChannelClose(AMQPMethod):
    """
    Request a channel close
    
    This method indicates that the sender wants to close the channel. This may be due to
    internal conditions (e.g. a forced shut-down) or due to an error handling a specific
    method, i.e. an exception. When a close is due to an exception, the sender provides
    the class and method id of the method which caused the exception.
    """
    CLASS = Channel
    NAME = u'close'
    CLASSNAME = u'channel'
    CLASS_INDEX = 20
    METHOD_INDEX = 40
    FULLNAME = u'channel.close'
    SYNCHRONOUS = True
    REPLY_WITH = [ChannelCloseOk]
    FIELDS = [
        (u'reply-code', u'reply-code', u'short'), 
        (u'reply-text', u'reply-text', u'shortstr'), 
        (u'class-id', u'class-id', u'short'),  # failing method class
        (u'method-id', u'method-id', u'short'),  # failing method ID
    ]

    def __init__(self, reply_code, reply_text, class_id, method_id):
        """
        Create frame channel.close

        :type reply_code: reply-code (as short)
        :type reply_text: reply-text (as shortstr)
        :param class_id: Failing method class
            When the close is provoked by a method exception, this is the class of the
            method.
        :type class_id: class-id (as short)
        :param method_id: Failing method id
            When the close is provoked by a method exception, this is the ID of the method.
        :type method_id: method-id (as short)
        """
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.class_id = class_id
        self.method_id = method_id

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ChannelCloseOk(AMQPMethod):
    """
    Confirm a channel close
    
    This method confirms a Channel.Close method and tells the recipient that it is safe
    to release resources for the channel.
    """
    CLASS = Channel
    NAME = u'close-ok'
    CLASSNAME = u'channel'
    CLASS_INDEX = 20
    METHOD_INDEX = 41
    FULLNAME = u'channel.close-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ChannelClose
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame channel.close-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ChannelFlow(AMQPMethod):
    """
    Enable/disable flow from peer
    
    This method asks the peer to pause or restart the flow of content data sent by
    a consumer. This is a simple flow-control mechanism that a peer can use to avoid
    overflowing its queues or otherwise finding itself receiving more messages than
    it can process. Note that this method is not intended for window control. It does
    not affect contents returned by Basic.Get-Ok methods.
    """
    CLASS = Channel
    NAME = u'flow'
    CLASSNAME = u'channel'
    CLASS_INDEX = 20
    METHOD_INDEX = 20
    FULLNAME = u'channel.flow'
    SYNCHRONOUS = True
    REPLY_WITH = [ChannelFlowOk]
    FIELDS = [
        (u'active', u'bit', u'bit'),  # start/stop content frames
    ]

    def __init__(self, active):
        """
        Create frame channel.flow

        :param active: Start/stop content frames
            If 1, the peer starts sending content frames. If 0, the peer stops sending
            content frames.
        :type active: bit (as bit)
        """
        self.active = active

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ChannelFlowOk(AMQPMethod):
    """
    Confirm a flow method
    
    Confirms to the peer that a flow command was received and processed.
    """
    CLASS = Channel
    NAME = u'flow-ok'
    CLASSNAME = u'channel'
    CLASS_INDEX = 20
    METHOD_INDEX = 21
    FULLNAME = u'channel.flow-ok'
    SYNCHRONOUS = False
    REPLY_WITH = []
    RESPONSE_TO = ChannelFlow
    FIELDS = [
        (u'active', u'bit', u'bit'),  # current flow setting
    ]

    def __init__(self, active):
        """
        Create frame channel.flow-ok

        :param active: Current flow setting
            Confirms the setting of the processed flow method: 1 means the peer will start
            sending or continue to send content frames; 0 means it will not.
        :type active: bit (as bit)
        """
        self.active = active

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ChannelOpen(AMQPMethod):
    """
    Open a channel for use
    
    This method opens a channel to the server.
    """
    CLASS = Channel
    NAME = u'open'
    CLASSNAME = u'channel'
    CLASS_INDEX = 20
    METHOD_INDEX = 10
    FULLNAME = u'channel.open'
    SYNCHRONOUS = True
    REPLY_WITH = [ChannelOpenOk]
    FIELDS = [
        (u'reserved-1', u'shortstr', u'shortstr'), 
    ]

    def __init__(self):
        """
        Create frame channel.open

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ChannelOpenOk(AMQPMethod):
    """
    Signal that the channel is ready
    
    This method signals to the client that the channel is ready for use.
    """
    CLASS = Channel
    NAME = u'open-ok'
    CLASSNAME = u'channel'
    CLASS_INDEX = 20
    METHOD_INDEX = 11
    FULLNAME = u'channel.open-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ChannelOpen
    FIELDS = [
        (u'reserved-1', u'longstr', u'longstr'), 
    ]

    def __init__(self):
        """
        Create frame channel.open-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()

class Exchange(AMQPClass):
    """
    Exchanges match and distribute messages across queues. exchanges can be configured in
    
    the server or declared at runtime.
    """
    NAME = u'exchange'
    INDEX = 40


class ExchangeDeclare(AMQPMethod):
    """
    Verify exchange exists, create if needed
    
    This method creates an exchange if it does not already exist, and if the exchange
    exists, verifies that it is of the correct and expected class.
    """
    CLASS = Exchange
    NAME = u'declare'
    CLASSNAME = u'exchange'
    CLASS_INDEX = 40
    METHOD_INDEX = 10
    FULLNAME = u'exchange.declare'
    SYNCHRONOUS = True
    REPLY_WITH = [ExchangeDeclareOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'exchange', u'exchange-name', u'shortstr'), 
        (u'type', u'shortstr', u'shortstr'),  # exchange type
        (u'passive', u'bit', u'bit'),  # do not create exchange
        (u'durable', u'bit', u'bit'),  # request a durable exchange
        (u'reserved-2', u'bit', u'bit'), 
        (u'reserved-3', u'bit', u'bit'), 
        (u'no-wait', u'no-wait', u'bit'), 
        (u'arguments', u'table', u'table'),  # arguments for declaration
    ]

    def __init__(self, exchange, type, passive, durable, no_wait, arguments):
        """
        Create frame exchange.declare

        :param exchange: Exchange names starting with "amq." are reserved for pre-declared and
            standardised exchanges. The client MAY declare an exchange starting with
            "amq." if the passive option is set, or the exchange already exists.
        :type exchange: exchange-name (as shortstr)
        :param type: Exchange type
            Each exchange belongs to one of a set of exchange types implemented by the
            server. The exchange types define the functionality of the exchange - i.e. how
            messages are routed through it. It is not valid or meaningful to attempt to
            change the type of an existing exchange.
        :type type: shortstr (as shortstr)
        :param passive: Do not create exchange
            If set, the server will reply with Declare-Ok if the exchange already
            exists with the same name, and raise an error if not.  The client can
            use this to check whether an exchange exists without modifying the
            server state. When set, all other method fields except name and no-wait
            are ignored.  A declare with both passive and no-wait has no effect.
            Arguments are compared for semantic equivalence.
        :type passive: bit (as bit)
        :param durable: Request a durable exchange
            If set when creating a new exchange, the exchange will be marked as durable.
            Durable exchanges remain active when a server restarts. Non-durable exchanges
            (transient exchanges) are purged if/when a server restarts.
        :type durable: bit (as bit)
        :type no_wait: no-wait (as bit)
        :param arguments: Arguments for declaration
            A set of arguments for the declaration. The syntax and semantics of these
            arguments depends on the server implementation.
        :type arguments: table (as table)
        """
        self.exchange = exchange
        self.type = type
        self.passive = passive
        self.durable = durable
        self.no_wait = no_wait
        self.arguments = arguments

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ExchangeDelete(AMQPMethod):
    """
    Delete an exchange
    
    This method deletes an exchange. When an exchange is deleted all queue bindings on
    the exchange are cancelled.
    """
    CLASS = Exchange
    NAME = u'delete'
    CLASSNAME = u'exchange'
    CLASS_INDEX = 40
    METHOD_INDEX = 20
    FULLNAME = u'exchange.delete'
    SYNCHRONOUS = True
    REPLY_WITH = [ExchangeDeleteOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'exchange', u'exchange-name', u'shortstr'), 
        (u'if-unused', u'bit', u'bit'),  # delete only if unused
        (u'no-wait', u'no-wait', u'bit'), 
    ]

    def __init__(self, exchange, if_unused, no_wait):
        """
        Create frame exchange.delete

        :param exchange:             The client must not attempt to delete an exchange that does not exist.

        :type exchange: exchange-name (as shortstr)
        :param if_unused: Delete only if unused
            If set, the server will only delete the exchange if it has no queue bindings. If
            the exchange has queue bindings the server does not delete it but raises a
            channel exception instead.
        :type if_unused: bit (as bit)
        :type no_wait: no-wait (as bit)
        """
        self.exchange = exchange
        self.if_unused = if_unused
        self.no_wait = no_wait

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ExchangeDeclareOk(AMQPMethod):
    """
    Confirm exchange declaration
    
    This method confirms a Declare method and confirms the name of the exchange,
    essential for automatically-named exchanges.
    """
    CLASS = Exchange
    NAME = u'declare-ok'
    CLASSNAME = u'exchange'
    CLASS_INDEX = 40
    METHOD_INDEX = 11
    FULLNAME = u'exchange.declare-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ExchangeDeclare
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame exchange.declare-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class ExchangeDeleteOk(AMQPMethod):
    """
    Confirm deletion of an exchange
    
    This method confirms the deletion of an exchange.
    """
    CLASS = Exchange
    NAME = u'delete-ok'
    CLASSNAME = u'exchange'
    CLASS_INDEX = 40
    METHOD_INDEX = 21
    FULLNAME = u'exchange.delete-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = ExchangeDelete
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame exchange.delete-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()

class Queue(AMQPClass):
    """
    Queues store and forward messages. queues can be configured in the server or created at
    
    runtime. Queues must be attached to at least one exchange in order to receive messages
    from publishers.
    """
    NAME = u'queue'
    INDEX = 50


class QueueBind(AMQPMethod):
    """
    Bind queue to an exchange
    
    This method binds a queue to an exchange. Until a queue is bound it will not
    receive any messages. In a classic messaging model, store-and-forward queues
    are bound to a direct exchange and subscription queues are bound to a topic
    exchange.
    """
    CLASS = Queue
    NAME = u'bind'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 20
    FULLNAME = u'queue.bind'
    SYNCHRONOUS = True
    REPLY_WITH = [QueueBindOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'queue', u'queue-name', u'shortstr'), 
        (u'exchange', u'exchange-name', u'shortstr'),  # name of the exchange to bind to
        (u'routing-key', u'shortstr', u'shortstr'),  # message routing key
        (u'no-wait', u'no-wait', u'bit'), 
        (u'arguments', u'table', u'table'),  # arguments for binding
    ]

    def __init__(self, queue, exchange, routing_key, no_wait, arguments):
        """
        Create frame queue.bind

        :param queue:             Specifies the name of the queue to bind.

        :type queue: queue-name (as shortstr)
        :param exchange: Name of the exchange to bind to
            A client MUST NOT be allowed to bind a queue to a non-existent exchange.
        :type exchange: exchange-name (as shortstr)
        :param routing_key: Message routing key
            Specifies the routing key for the binding. The routing key is used for routing
            messages depending on the exchange configuration. Not all exchanges use a
            routing key - refer to the specific exchange documentation.  If the queue name
            is empty, the server uses the last queue declared on the channel.  If the
            routing key is also empty, the server uses this queue name for the routing
            key as well.  If the queue name is provided but the routing key is empty, the
            server does the binding with that empty routing key.  The meaning of empty
            routing keys depends on the exchange implementation.
        :type routing_key: shortstr (as shortstr)
        :type no_wait: no-wait (as bit)
        :param arguments: Arguments for binding
            A set of arguments for the binding. The syntax and semantics of these arguments
            depends on the exchange class.
        :type arguments: table (as table)
        """
        self.queue = queue
        self.exchange = exchange
        self.routing_key = routing_key
        self.no_wait = no_wait
        self.arguments = arguments

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueueBindOk(AMQPMethod):
    """
    Confirm bind successful
    
    This method confirms that the bind was successful.
    """
    CLASS = Queue
    NAME = u'bind-ok'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 21
    FULLNAME = u'queue.bind-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = QueueBind
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame queue.bind-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueueDeclare(AMQPMethod):
    """
    Declare queue, create if needed
    
    This method creates or checks a queue. When creating a new queue the client can
    specify various properties that control the durability of the queue and its
    contents, and the level of sharing for the queue.
    """
    CLASS = Queue
    NAME = u'declare'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 10
    FULLNAME = u'queue.declare'
    SYNCHRONOUS = True
    REPLY_WITH = [QueueDeclareOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'queue', u'queue-name', u'shortstr'), 
        (u'passive', u'bit', u'bit'),  # do not create queue
        (u'durable', u'bit', u'bit'),  # request a durable queue
        (u'exclusive', u'bit', u'bit'),  # request an exclusive queue
        (u'auto-delete', u'bit', u'bit'),  # auto-delete queue when unused
        (u'no-wait', u'no-wait', u'bit'), 
        (u'arguments', u'table', u'table'),  # arguments for declaration
    ]

    def __init__(self, queue, passive, durable, exclusive, auto_delete, no_wait, arguments):
        """
        Create frame queue.declare

        :param queue: The queue name may be empty, in which case the server must create a new
            queue with a unique generated name and return this to the client in the
            Declare-Ok method.
        :type queue: queue-name (as shortstr)
        :param passive: Do not create queue
            If set, the server will reply with Declare-Ok if the queue already
            exists with the same name, and raise an error if not.  The client can
            use this to check whether a queue exists without modifying the
            server state.  When set, all other method fields except name and no-wait
            are ignored.  A declare with both passive and no-wait has no effect.
            Arguments are compared for semantic equivalence.
        :type passive: bit (as bit)
        :param durable: Request a durable queue
            If set when creating a new queue, the queue will be marked as durable. Durable
            queues remain active when a server restarts. Non-durable queues (transient
            queues) are purged if/when a server restarts. Note that durable queues do not
            necessarily hold persistent messages, although it does not make sense to send
            persistent messages to a transient queue.
        :type durable: bit (as bit)
        :param exclusive: Request an exclusive queue
            Exclusive queues may only be accessed by the current connection, and are
            deleted when that connection closes.  Passive declaration of an exclusive
            queue by other connections are not allowed.
        :type exclusive: bit (as bit)
        :param auto_delete: Auto-delete queue when unused
            If set, the queue is deleted when all consumers have finished using it.  The last
            consumer can be cancelled either explicitly or because its channel is closed. If
            there was no consumer ever on the queue, it won't be deleted.  Applications can
            explicitly delete auto-delete queues using the Delete method as normal.
        :type auto_delete: bit (as bit)
        :type no_wait: no-wait (as bit)
        :param arguments: Arguments for declaration
            A set of arguments for the declaration. The syntax and semantics of these
            arguments depends on the server implementation.
        :type arguments: table (as table)
        """
        self.queue = queue
        self.passive = passive
        self.durable = durable
        self.exclusive = exclusive
        self.auto_delete = auto_delete
        self.no_wait = no_wait
        self.arguments = arguments

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueueDelete(AMQPMethod):
    """
    Delete a queue
    
    This method deletes a queue. When a queue is deleted any pending messages are sent
    to a dead-letter queue if this is defined in the server configuration, and all
    consumers on the queue are cancelled.
    """
    CLASS = Queue
    NAME = u'delete'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 40
    FULLNAME = u'queue.delete'
    SYNCHRONOUS = True
    REPLY_WITH = [QueueDeleteOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'queue', u'queue-name', u'shortstr'), 
        (u'if-unused', u'bit', u'bit'),  # delete only if unused
        (u'if-empty', u'bit', u'bit'),  # delete only if empty
        (u'no-wait', u'no-wait', u'bit'), 
    ]

    def __init__(self, queue, if_unused, if_empty, no_wait):
        """
        Create frame queue.delete

        :param queue:             Specifies the name of the queue to delete.

        :type queue: queue-name (as shortstr)
        :param if_unused: Delete only if unused
            If set, the server will only delete the queue if it has no consumers. If the
            queue has consumers the server does does not delete it but raises a channel
            exception instead.
        :type if_unused: bit (as bit)
        :param if_empty: Delete only if empty
            If set, the server will only delete the queue if it has no messages.
        :type if_empty: bit (as bit)
        :type no_wait: no-wait (as bit)
        """
        self.queue = queue
        self.if_unused = if_unused
        self.if_empty = if_empty
        self.no_wait = no_wait

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueueDeclareOk(AMQPMethod):
    """
    Confirms a queue definition
    
    This method confirms a Declare method and confirms the name of the queue, essential
    for automatically-named queues.
    """
    CLASS = Queue
    NAME = u'declare-ok'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 11
    FULLNAME = u'queue.declare-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = QueueDeclare
    FIELDS = [
        (u'queue', u'queue-name', u'shortstr'), 
        (u'message-count', u'message-count', u'long'), 
        (u'consumer-count', u'long', u'long'),  # number of consumers
    ]

    def __init__(self, queue, message_count, consumer_count):
        """
        Create frame queue.declare-ok

        :param queue: Reports the name of the queue. if the server generated a queue name, this field
            contains that name.
        :type queue: queue-name (as shortstr)
        :type message_count: message-count (as long)
        :param consumer_count: Number of consumers
            Reports the number of active consumers for the queue. Note that consumers can
            suspend activity (Channel.Flow) in which case they do not appear in this count.
        :type consumer_count: long (as long)
        """
        self.queue = queue
        self.message_count = message_count
        self.consumer_count = consumer_count

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueueDeleteOk(AMQPMethod):
    """
    Confirm deletion of a queue
    
    This method confirms the deletion of a queue.
    """
    CLASS = Queue
    NAME = u'delete-ok'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 41
    FULLNAME = u'queue.delete-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = QueueDelete
    FIELDS = [
        (u'message-count', u'message-count', u'long'), 
    ]

    def __init__(self, message_count):
        """
        Create frame queue.delete-ok

        :param message_count:             Reports the number of messages deleted.

        :type message_count: message-count (as long)
        """
        self.message_count = message_count

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueuePurge(AMQPMethod):
    """
    Purge a queue
    
    This method removes all messages from a queue which are not awaiting
    acknowledgment.
    """
    CLASS = Queue
    NAME = u'purge'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 30
    FULLNAME = u'queue.purge'
    SYNCHRONOUS = True
    REPLY_WITH = [QueuePurgeOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'queue', u'queue-name', u'shortstr'), 
        (u'no-wait', u'no-wait', u'bit'), 
    ]

    def __init__(self, queue, no_wait):
        """
        Create frame queue.purge

        :param queue:             Specifies the name of the queue to purge.

        :type queue: queue-name (as shortstr)
        :type no_wait: no-wait (as bit)
        """
        self.queue = queue
        self.no_wait = no_wait

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueuePurgeOk(AMQPMethod):
    """
    Confirms a queue purge
    
    This method confirms the purge of a queue.
    """
    CLASS = Queue
    NAME = u'purge-ok'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 31
    FULLNAME = u'queue.purge-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = QueuePurge
    FIELDS = [
        (u'message-count', u'message-count', u'long'), 
    ]

    def __init__(self, message_count):
        """
        Create frame queue.purge-ok

        :param message_count:             Reports the number of messages purged.

        :type message_count: message-count (as long)
        """
        self.message_count = message_count

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueueUnbind(AMQPMethod):
    """
    Unbind a queue from an exchange
    
    This method unbinds a queue from an exchange.
    """
    CLASS = Queue
    NAME = u'unbind'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 50
    FULLNAME = u'queue.unbind'
    SYNCHRONOUS = True
    REPLY_WITH = [QueueUnbindOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'queue', u'queue-name', u'shortstr'), 
        (u'exchange', u'exchange-name', u'shortstr'), 
        (u'routing-key', u'shortstr', u'shortstr'),  # routing key of binding
        (u'arguments', u'table', u'table'),  # arguments of binding
    ]

    def __init__(self, queue, exchange, routing_key, arguments):
        """
        Create frame queue.unbind

        :param queue:             Specifies the name of the queue to unbind.

        :type queue: queue-name (as shortstr)
        :param exchange:             The name of the exchange to unbind from.

        :type exchange: exchange-name (as shortstr)
        :param routing_key: Routing key of binding
            Specifies the routing key of the binding to unbind.
        :type routing_key: shortstr (as shortstr)
        :param arguments: Arguments of binding
            Specifies the arguments of the binding to unbind.
        :type arguments: table (as table)
        """
        self.queue = queue
        self.exchange = exchange
        self.routing_key = routing_key
        self.arguments = arguments

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class QueueUnbindOk(AMQPMethod):
    """
    Confirm unbind successful
    
    This method confirms that the unbind was successful.
    """
    CLASS = Queue
    NAME = u'unbind-ok'
    CLASSNAME = u'queue'
    CLASS_INDEX = 50
    METHOD_INDEX = 51
    FULLNAME = u'queue.unbind-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = QueueUnbind
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame queue.unbind-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()

class Basic(AMQPClass):
    """
        The basic class provides methods that support an industry-standard messaging model.

    """
    NAME = u'basic'
    INDEX = 60


class BasicAck(AMQPMethod):
    """
    Acknowledge one or more messages
    
    This method acknowledges one or more messages delivered via the Deliver or Get-Ok
    methods. The client can ask to confirm a single message or a set of messages up to
    and including a specific message.
    """
    CLASS = Basic
    NAME = u'ack'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 80
    FULLNAME = u'basic.ack'
    SYNCHRONOUS = False
    REPLY_WITH = []
    FIELDS = [
        (u'delivery-tag', u'delivery-tag', u'longlong'), 
        (u'multiple', u'bit', u'bit'),  # acknowledge multiple messages
    ]

    def __init__(self, delivery_tag, multiple):
        """
        Create frame basic.ack

        :type delivery_tag: delivery-tag (as longlong)
        :param multiple: Acknowledge multiple messages
            If set to 1, the delivery tag is treated as "up to and including", so that the
            client can acknowledge multiple messages with a single method. If set to zero,
            the delivery tag refers to a single message. If the multiple field is 1, and the
            delivery tag is zero, tells the server to acknowledge all outstanding messages.
        :type multiple: bit (as bit)
        """
        self.delivery_tag = delivery_tag
        self.multiple = multiple

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicConsume(AMQPMethod):
    """
    Start a queue consumer
    
    This method asks the server to start a "consumer", which is a transient request for
    messages from a specific queue. Consumers last as long as the channel they were
    declared on, or until the client cancels them.
    """
    CLASS = Basic
    NAME = u'consume'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 20
    FULLNAME = u'basic.consume'
    SYNCHRONOUS = True
    REPLY_WITH = [BasicConsumeOk]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'queue', u'queue-name', u'shortstr'), 
        (u'consumer-tag', u'consumer-tag', u'shortstr'), 
        (u'no-local', u'no-local', u'bit'), 
        (u'no-ack', u'no-ack', u'bit'), 
        (u'exclusive', u'bit', u'bit'),  # request exclusive access
        (u'no-wait', u'no-wait', u'bit'), 
        (u'arguments', u'table', u'table'),  # arguments for declaration
    ]

    def __init__(self, queue, consumer_tag, no_local, no_ack, exclusive, no_wait, arguments):
        """
        Create frame basic.consume

        :param queue:             Specifies the name of the queue to consume from.

        :type queue: queue-name (as shortstr)
        :param consumer_tag: Specifies the identifier for the consumer. the consumer tag is local to a
            channel, so two clients can use the same consumer tags. If this field is
            empty the server will generate a unique tag.
        :type consumer_tag: consumer-tag (as shortstr)
        :type no_local: no-local (as bit)
        :type no_ack: no-ack (as bit)
        :param exclusive: Request exclusive access
            Request exclusive consumer access, meaning only this consumer can access the
            queue.
        :type exclusive: bit (as bit)
        :type no_wait: no-wait (as bit)
        :param arguments: Arguments for declaration
            A set of arguments for the consume. The syntax and semantics of these
            arguments depends on the server implementation.
        :type arguments: table (as table)
        """
        self.queue = queue
        self.consumer_tag = consumer_tag
        self.no_local = no_local
        self.no_ack = no_ack
        self.exclusive = exclusive
        self.no_wait = no_wait
        self.arguments = arguments

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicCancel(AMQPMethod):
    """
    End a queue consumer
    
    This method cancels a consumer. This does not affect already delivered
    messages, but it does mean the server will not send any more messages for
    that consumer. The client may receive an arbitrary number of messages in
    between sending the cancel method and receiving the cancel-ok reply.
    """
    CLASS = Basic
    NAME = u'cancel'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 30
    FULLNAME = u'basic.cancel'
    SYNCHRONOUS = True
    REPLY_WITH = [BasicCancelOk]
    FIELDS = [
        (u'consumer-tag', u'consumer-tag', u'shortstr'), 
        (u'no-wait', u'no-wait', u'bit'), 
    ]

    def __init__(self, consumer_tag, no_wait):
        """
        Create frame basic.cancel

        :type consumer_tag: consumer-tag (as shortstr)
        :type no_wait: no-wait (as bit)
        """
        self.consumer_tag = consumer_tag
        self.no_wait = no_wait

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicConsumeOk(AMQPMethod):
    """
    Confirm a new consumer
    
    The server provides the client with a consumer tag, which is used by the client
    for methods called on the consumer at a later stage.
    """
    CLASS = Basic
    NAME = u'consume-ok'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 21
    FULLNAME = u'basic.consume-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = BasicConsume
    FIELDS = [
        (u'consumer-tag', u'consumer-tag', u'shortstr'), 
    ]

    def __init__(self, consumer_tag):
        """
        Create frame basic.consume-ok

        :param consumer_tag:             Holds the consumer tag specified by the client or provided by the server.

        :type consumer_tag: consumer-tag (as shortstr)
        """
        self.consumer_tag = consumer_tag

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicCancelOk(AMQPMethod):
    """
    Confirm a cancelled consumer
    
    This method confirms that the cancellation was completed.
    """
    CLASS = Basic
    NAME = u'cancel-ok'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 31
    FULLNAME = u'basic.cancel-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = BasicCancel
    FIELDS = [
        (u'consumer-tag', u'consumer-tag', u'shortstr'), 
    ]

    def __init__(self, consumer_tag):
        """
        Create frame basic.cancel-ok

        :type consumer_tag: consumer-tag (as shortstr)
        """
        self.consumer_tag = consumer_tag

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicDeliver(AMQPMethod):
    """
    Notify the client of a consumer message
    
    This method delivers a message to the client, via a consumer. In the asynchronous
    message delivery model, the client starts a consumer using the Consume method, then
    the server responds with Deliver methods as and when messages arrive for that
    consumer.
    """
    CLASS = Basic
    NAME = u'deliver'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 60
    FULLNAME = u'basic.deliver'
    SYNCHRONOUS = False
    REPLY_WITH = []
    FIELDS = [
        (u'consumer-tag', u'consumer-tag', u'shortstr'), 
        (u'delivery-tag', u'delivery-tag', u'longlong'), 
        (u'redelivered', u'redelivered', u'bit'), 
        (u'exchange', u'exchange-name', u'shortstr'), 
        (u'routing-key', u'shortstr', u'shortstr'),  # Message routing key
    ]

    def __init__(self, consumer_tag, delivery_tag, redelivered, exchange, routing_key):
        """
        Create frame basic.deliver

        :type consumer_tag: consumer-tag (as shortstr)
        :type delivery_tag: delivery-tag (as longlong)
        :type redelivered: redelivered (as bit)
        :param exchange: Specifies the name of the exchange that the message was originally published to.
            May be empty, indicating the default exchange.
        :type exchange: exchange-name (as shortstr)
        :param routing_key: Message routing key
            Specifies the routing key name specified when the message was published.
        :type routing_key: shortstr (as shortstr)
        """
        self.consumer_tag = consumer_tag
        self.delivery_tag = delivery_tag
        self.redelivered = redelivered
        self.exchange = exchange
        self.routing_key = routing_key

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicGet(AMQPMethod):
    """
    Direct access to a queue
    
    This method provides a direct access to the messages in a queue using a synchronous
    dialogue that is designed for specific types of application where synchronous
    functionality is more important than performance.
    """
    CLASS = Basic
    NAME = u'get'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 70
    FULLNAME = u'basic.get'
    SYNCHRONOUS = True
    REPLY_WITH = [BasicGetOk, BasicGetEmpty]
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'queue', u'queue-name', u'shortstr'), 
        (u'no-ack', u'no-ack', u'bit'), 
    ]

    def __init__(self, queue, no_ack):
        """
        Create frame basic.get

        :param queue:             Specifies the name of the queue to get a message from.

        :type queue: queue-name (as shortstr)
        :type no_ack: no-ack (as bit)
        """
        self.queue = queue
        self.no_ack = no_ack

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicGetOk(AMQPMethod):
    """
    Provide client with a message
    
    This method delivers a message to the client following a get method. A message
    delivered by 'get-ok' must be acknowledged unless the no-ack option was set in the
    get method.
    """
    CLASS = Basic
    NAME = u'get-ok'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 71
    FULLNAME = u'basic.get-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = BasicGet
    FIELDS = [
        (u'delivery-tag', u'delivery-tag', u'longlong'), 
        (u'redelivered', u'redelivered', u'bit'), 
        (u'exchange', u'exchange-name', u'shortstr'), 
        (u'routing-key', u'shortstr', u'shortstr'),  # Message routing key
        (u'message-count', u'message-count', u'long'), 
    ]

    def __init__(self, delivery_tag, redelivered, exchange, routing_key, message_count):
        """
        Create frame basic.get-ok

        :type delivery_tag: delivery-tag (as longlong)
        :type redelivered: redelivered (as bit)
        :param exchange: Specifies the name of the exchange that the message was originally published to.
            If empty, the message was published to the default exchange.
        :type exchange: exchange-name (as shortstr)
        :param routing_key: Message routing key
            Specifies the routing key name specified when the message was published.
        :type routing_key: shortstr (as shortstr)
        :type message_count: message-count (as long)
        """
        self.delivery_tag = delivery_tag
        self.redelivered = redelivered
        self.exchange = exchange
        self.routing_key = routing_key
        self.message_count = message_count

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicGetEmpty(AMQPMethod):
    """
    Indicate no messages available
    
    This method tells the client that the queue has no messages available for the
    client.
    """
    CLASS = Basic
    NAME = u'get-empty'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 72
    FULLNAME = u'basic.get-empty'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = BasicGet
    FIELDS = [
        (u'reserved-1', u'shortstr', u'shortstr'), 
    ]

    def __init__(self):
        """
        Create frame basic.get-empty

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicPublish(AMQPMethod):
    """
    Publish a message
    
    This method publishes a message to a specific exchange. The message will be routed
    to queues as defined by the exchange configuration and distributed to any active
    consumers when the transaction, if any, is committed.
    """
    CLASS = Basic
    NAME = u'publish'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 40
    FULLNAME = u'basic.publish'
    SYNCHRONOUS = False
    REPLY_WITH = []
    FIELDS = [
        (u'reserved-1', u'short', u'short'), 
        (u'exchange', u'exchange-name', u'shortstr'), 
        (u'routing-key', u'shortstr', u'shortstr'),  # Message routing key
        (u'mandatory', u'bit', u'bit'),  # indicate mandatory routing
        (u'immediate', u'bit', u'bit'),  # request immediate delivery
    ]

    def __init__(self, exchange, routing_key, mandatory, immediate):
        """
        Create frame basic.publish

        :param exchange: Specifies the name of the exchange to publish to. the exchange name can be
            empty, meaning the default exchange. If the exchange name is specified, and that
            exchange does not exist, the server will raise a channel exception.
        :type exchange: exchange-name (as shortstr)
        :param routing_key: Message routing key
            Specifies the routing key for the message. The routing key is used for routing
            messages depending on the exchange configuration.
        :type routing_key: shortstr (as shortstr)
        :param mandatory: Indicate mandatory routing
            This flag tells the server how to react if the message cannot be routed to a
            queue. If this flag is set, the server will return an unroutable message with a
            Return method. If this flag is zero, the server silently drops the message.
        :type mandatory: bit (as bit)
        :param immediate: Request immediate delivery
            This flag tells the server how to react if the message cannot be routed to a
            queue consumer immediately. If this flag is set, the server will return an
            undeliverable message with a Return method. If this flag is zero, the server
            will queue the message, but with no guarantee that it will ever be consumed.
        :type immediate: bit (as bit)
        """
        self.exchange = exchange
        self.routing_key = routing_key
        self.mandatory = mandatory
        self.immediate = immediate

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicQos(AMQPMethod):
    """
    Specify quality of service
    
    This method requests a specific quality of service. The QoS can be specified for the
    current channel or for all channels on the connection. The particular properties and
    semantics of a qos method always depend on the content class semantics. Though the
    qos method could in principle apply to both peers, it is currently meaningful only
    for the server.
    """
    CLASS = Basic
    NAME = u'qos'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 10
    FULLNAME = u'basic.qos'
    SYNCHRONOUS = True
    REPLY_WITH = [BasicQosOk]
    FIELDS = [
        (u'prefetch-size', u'long', u'long'),  # prefetch window in octets
        (u'prefetch-count', u'short', u'short'),  # prefetch window in messages
        (u'global', u'bit', u'bit'),  # apply to entire connection
    ]

    def __init__(self, prefetch_size, prefetch_count, global_):
        """
        Create frame basic.qos

        :param prefetch_size: Prefetch window in octets
            The client can request that messages be sent in advance so that when the client
            finishes processing a message, the following message is already held locally,
            rather than needing to be sent down the channel. Prefetching gives a performance
            improvement. This field specifies the prefetch window size in octets. The server
            will send a message in advance if it is equal to or smaller in size than the
            available prefetch size (and also falls into other prefetch limits). May be set
            to zero, meaning "no specific limit", although other prefetch limits may still
            apply. The prefetch-size is ignored if the no-ack option is set.
        :type prefetch_size: long (as long)
        :param prefetch_count: Prefetch window in messages
            Specifies a prefetch window in terms of whole messages. This field may be used
            in combination with the prefetch-size field; a message will only be sent in
            advance if both prefetch windows (and those at the channel and connection level)
            allow it. The prefetch-count is ignored if the no-ack option is set.
        :type prefetch_count: short (as short)
        :param global_: Apply to entire connection
            By default the QoS settings apply to the current channel only. If this field is
            set, they are applied to the entire connection.
        :type global_: bit (as bit)
        """
        self.prefetch_size = prefetch_size
        self.prefetch_count = prefetch_count
        self.global_ = global_

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicQosOk(AMQPMethod):
    """
    Confirm the requested qos
    
    This method tells the client that the requested QoS levels could be handled by the
    server. The requested QoS applies to all active consumers until a new QoS is
    defined.
    """
    CLASS = Basic
    NAME = u'qos-ok'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 11
    FULLNAME = u'basic.qos-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = BasicQos
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame basic.qos-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicReturn(AMQPMethod):
    """
    Return a failed message
    
    This method returns an undeliverable message that was published with the "immediate"
    flag set, or an unroutable message published with the "mandatory" flag set. The
    reply code and text provide information about the reason that the message was
    undeliverable.
    """
    CLASS = Basic
    NAME = u'return'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 50
    FULLNAME = u'basic.return'
    SYNCHRONOUS = False
    REPLY_WITH = []
    FIELDS = [
        (u'reply-code', u'reply-code', u'short'), 
        (u'reply-text', u'reply-text', u'shortstr'), 
        (u'exchange', u'exchange-name', u'shortstr'), 
        (u'routing-key', u'shortstr', u'shortstr'),  # Message routing key
    ]

    def __init__(self, reply_code, reply_text, exchange, routing_key):
        """
        Create frame basic.return

        :type reply_code: reply-code (as short)
        :type reply_text: reply-text (as shortstr)
        :param exchange: Specifies the name of the exchange that the message was originally published
            to.  May be empty, meaning the default exchange.
        :type exchange: exchange-name (as shortstr)
        :param routing_key: Message routing key
            Specifies the routing key name specified when the message was published.
        :type routing_key: shortstr (as shortstr)
        """
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.exchange = exchange
        self.routing_key = routing_key

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicReject(AMQPMethod):
    """
    Reject an incoming message
    
    This method allows a client to reject a message. It can be used to interrupt and
    cancel large incoming messages, or return untreatable messages to their original
    queue.
    """
    CLASS = Basic
    NAME = u'reject'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 90
    FULLNAME = u'basic.reject'
    SYNCHRONOUS = False
    REPLY_WITH = []
    FIELDS = [
        (u'delivery-tag', u'delivery-tag', u'longlong'), 
        (u'requeue', u'bit', u'bit'),  # requeue the message
    ]

    def __init__(self, delivery_tag, requeue):
        """
        Create frame basic.reject

        :type delivery_tag: delivery-tag (as longlong)
        :param requeue: Requeue the message
            If requeue is true, the server will attempt to requeue the message.  If requeue
            is false or the requeue  attempt fails the messages are discarded or dead-lettered.
        :type requeue: bit (as bit)
        """
        self.delivery_tag = delivery_tag
        self.requeue = requeue

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicRecoverAsync(AMQPMethod):
    """
    Redeliver unacknowledged messages
    
    This method asks the server to redeliver all unacknowledged messages on a
    specified channel. Zero or more messages may be redelivered.  This method
    is deprecated in favour of the synchronous Recover/Recover-Ok.
    """
    CLASS = Basic
    NAME = u'recover-async'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 100
    FULLNAME = u'basic.recover-async'
    SYNCHRONOUS = False
    REPLY_WITH = []
    FIELDS = [
        (u'requeue', u'bit', u'bit'),  # requeue the message
    ]

    def __init__(self, requeue):
        """
        Create frame basic.recover-async

        :param requeue: Requeue the message
            If this field is zero, the message will be redelivered to the original
            recipient. If this bit is 1, the server will attempt to requeue the message,
            potentially then delivering it to an alternative subscriber.
        :type requeue: bit (as bit)
        """
        self.requeue = requeue

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicRecover(AMQPMethod):
    """
    Redeliver unacknowledged messages
    
    This method asks the server to redeliver all unacknowledged messages on a
    specified channel. Zero or more messages may be redelivered.  This method
    replaces the asynchronous Recover.
    """
    CLASS = Basic
    NAME = u'recover'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 110
    FULLNAME = u'basic.recover'
    SYNCHRONOUS = False
    REPLY_WITH = []
    FIELDS = [
        (u'requeue', u'bit', u'bit'),  # requeue the message
    ]

    def __init__(self, requeue):
        """
        Create frame basic.recover

        :param requeue: Requeue the message
            If this field is zero, the message will be redelivered to the original
            recipient. If this bit is 1, the server will attempt to requeue the message,
            potentially then delivering it to an alternative subscriber.
        :type requeue: bit (as bit)
        """
        self.requeue = requeue

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class BasicRecoverOk(AMQPMethod):
    """
    Confirm recovery
    
    This method acknowledges a Basic.Recover method.
    """
    CLASS = Basic
    NAME = u'recover-ok'
    CLASSNAME = u'basic'
    CLASS_INDEX = 60
    METHOD_INDEX = 111
    FULLNAME = u'basic.recover-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame basic.recover-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()

class Tx(AMQPClass):
    """
    The tx class allows publish and ack operations to be batched into atomic
    
    units of work.  The intention is that all publish and ack requests issued
    within a transaction will complete successfully or none of them will.
    Servers SHOULD implement atomic transactions at least where all publish
    or ack requests affect a single queue.  Transactions that cover multiple
    queues may be non-atomic, given that queues can be created and destroyed
    asynchronously, and such events do not form part of any transaction.
    Further, the behaviour of transactions with respect to the immediate and
    mandatory flags on Basic.Publish methods is not defined.
    """
    NAME = u'tx'
    INDEX = 90


class TxCommit(AMQPMethod):
    """
    Commit the current transaction
    
    This method commits all message publications and acknowledgments performed in
    the current transaction.  A new transaction starts immediately after a commit.
    """
    CLASS = Tx
    NAME = u'commit'
    CLASSNAME = u'tx'
    CLASS_INDEX = 90
    METHOD_INDEX = 20
    FULLNAME = u'tx.commit'
    SYNCHRONOUS = True
    REPLY_WITH = [TxCommitOk]
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame tx.commit

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class TxCommitOk(AMQPMethod):
    """
    Confirm a successful commit
    
    This method confirms to the client that the commit succeeded. Note that if a commit
    fails, the server raises a channel exception.
    """
    CLASS = Tx
    NAME = u'commit-ok'
    CLASSNAME = u'tx'
    CLASS_INDEX = 90
    METHOD_INDEX = 21
    FULLNAME = u'tx.commit-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = TxCommit
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame tx.commit-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class TxRollback(AMQPMethod):
    """
    Abandon the current transaction
    
    This method abandons all message publications and acknowledgments performed in
    the current transaction. A new transaction starts immediately after a rollback.
    Note that unacked messages will not be automatically redelivered by rollback;
    if that is required an explicit recover call should be issued.
    """
    CLASS = Tx
    NAME = u'rollback'
    CLASSNAME = u'tx'
    CLASS_INDEX = 90
    METHOD_INDEX = 30
    FULLNAME = u'tx.rollback'
    SYNCHRONOUS = True
    REPLY_WITH = [TxRollbackOk]
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame tx.rollback

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class TxRollbackOk(AMQPMethod):
    """
    Confirm successful rollback
    
    This method confirms to the client that the rollback succeeded. Note that if an
    rollback fails, the server raises a channel exception.
    """
    CLASS = Tx
    NAME = u'rollback-ok'
    CLASSNAME = u'tx'
    CLASS_INDEX = 90
    METHOD_INDEX = 31
    FULLNAME = u'tx.rollback-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = TxRollback
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame tx.rollback-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class TxSelect(AMQPMethod):
    """
    Select standard transaction mode
    
    This method sets the channel to use standard transactions. The client must use this
    method at least once on a channel before using the Commit or Rollback methods.
    """
    CLASS = Tx
    NAME = u'select'
    CLASSNAME = u'tx'
    CLASS_INDEX = 90
    METHOD_INDEX = 10
    FULLNAME = u'tx.select'
    SYNCHRONOUS = True
    REPLY_WITH = [TxSelectOk]
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame tx.select

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


class TxSelectOk(AMQPMethod):
    """
    Confirm transaction mode
    
    This method confirms to the client that the channel was successfully set to use
    standard transactions.
    """
    CLASS = Tx
    NAME = u'select-ok'
    CLASSNAME = u'tx'
    CLASS_INDEX = 90
    METHOD_INDEX = 11
    FULLNAME = u'tx.select-ok'
    SYNCHRONOUS = True
    REPLY_WITH = []
    RESPONSE_TO = TxSelect
    FIELDS = [
    ]

    def __init__(self):
        """
        Create frame tx.select-ok

        """

    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()


IDENT_TO_METHOD = {
    (90, 21): TxCommitOk,
    (60, 100): BasicRecoverAsync,
    (10, 11): ConnectionStartOk,
    (60, 40): BasicPublish,
    (60, 50): BasicReturn,
    (10, 51): ConnectionCloseOk,
    (20, 20): ChannelFlow,
    (60, 21): BasicConsumeOk,
    (10, 21): ConnectionSecureOk,
    (90, 30): TxRollback,
    (90, 10): TxSelect,
    (50, 11): QueueDeclareOk,
    (60, 70): BasicGet,
    (90, 11): TxSelectOk,
    (10, 30): ConnectionTune,
    (60, 11): BasicQosOk,
    (60, 80): BasicAck,
    (20, 21): ChannelFlowOk,
    (60, 60): BasicDeliver,
    (90, 31): TxRollbackOk,
    (20, 40): ChannelClose,
    (60, 71): BasicGetOk,
    (50, 30): QueuePurge,
    (10, 31): ConnectionTuneOk,
    (10, 40): ConnectionOpen,
    (60, 30): BasicCancel,
    (50, 50): QueueUnbind,
    (40, 10): ExchangeDeclare,
    (10, 50): ConnectionClose,
    (20, 10): ChannelOpen,
    (20, 41): ChannelCloseOk,
    (60, 110): BasicRecover,
    (60, 90): BasicReject,
    (50, 31): QueuePurgeOk,
    (50, 40): QueueDelete,
    (40, 20): ExchangeDelete,
    (50, 20): QueueBind,
    (10, 41): ConnectionOpenOk,
    (60, 31): BasicCancelOk,
    (90, 20): TxCommit,
    (10, 10): ConnectionStart,
    (60, 10): BasicQos,
    (40, 11): ExchangeDeclareOk,
    (40, 21): ExchangeDeleteOk,
    (20, 11): ChannelOpenOk,
    (60, 72): BasicGetEmpty,
    (60, 111): BasicRecoverOk,
    (60, 20): BasicConsume,
    (10, 20): ConnectionSecure,
    (50, 41): QueueDeleteOk,
    (50, 51): QueueUnbindOk,
    (50, 21): QueueBindOk,
    (50, 10): QueueDeclare,
}

