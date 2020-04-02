# coding=UTF-8
from __future__ import print_function, absolute_import

"""
A Python version of the AMQP machine-readable specification.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See compile_definitions for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016-2018 DMS Serwis s.c., 2018-2020 SMOK sp. z o.o.


###########################################################
# IMPORTANT NOTE                                          #
# Type of field may depend on the origin of packet.       #
# strings will be memoryviews if we received the packet   #
# while they may be bytes if we created it                #
#                                                         #
# this has some use - speed :D                            #
###########################################################
tl;dr - you received something and it's supposed to be a
binary string? It's a memoryview all right.
Only thing that isn't are field names in tables.
"""

import struct
import collections
import logging
import six
import typing as tp

from coolamqp.framing.base import AMQPClass, AMQPMethodPayload, AMQPContentPropertyList
from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size
from coolamqp.framing.compilation import compile_particular_content_property_list_class

logger = logging.getLogger(__name__)

Field = collections.namedtuple('Field',
                               ('name', 'type', 'basic_type', 'reserved'))

# Core constants
FRAME_METHOD = 1
FRAME_METHOD_BYTE = b'\x01'

FRAME_HEADER = 2
FRAME_HEADER_BYTE = b'\x02'

FRAME_BODY = 3
FRAME_BODY_BYTE = b'\x03'

FRAME_HEARTBEAT = 8
FRAME_HEARTBEAT_BYTE = b'\x08'

FRAME_MIN_SIZE = 4096

FRAME_END = 206
FRAME_END_BYTE = b'\xce'

# Indicates that the method completed successfully. This reply code is
# reserved for future use - the current protocol design does not use
# positive
# confirmation and reply codes are sent only in case of an error.
REPLY_SUCCESS = 200
REPLY_SUCCESS_BYTE = b'\xc8'

# The client attempted to transfer content larger than the server
# could accept
# at the present time. The client may retry at a later time.
CONTENT_TOO_LARGE = 311

# When the exchange cannot deliver to a consumer when the immediate
# flag is
# set. As a result of pending data on the queue or the absence of any
# consumers of the queue.
NO_CONSUMERS = 313

# An operator intervened to close the connection for some reason. The
# client
# may retry at some later date.
CONNECTION_FORCED = 320

# The client tried to work with an unknown virtual host.
INVALID_PATH = 402

# The client attempted to work with a server entity to which it has no
# access due to security settings.
ACCESS_REFUSED = 403

# The client attempted to work with a server entity that does not
# exist.
NOT_FOUND = 404

# The client attempted to work with a server entity to which it has no
# access because another client is working with it.
RESOURCE_LOCKED = 405

# The client requested a method that was not allowed because some
# precondition
# failed.
PRECONDITION_FAILED = 406

# The sender sent a malformed frame that the recipient could not
# decode.
# This strongly implies a programming error in the sending peer.
FRAME_ERROR = 501

# The sender sent a frame that contained illegal values for one or
# more
# fields. This strongly implies a programming error in the sending
# peer.
SYNTAX_ERROR = 502

# The client sent an invalid sequence of frames, attempting to perform
# an
# operation that was considered invalid by the server. This usually
# implies
# a programming error in the client.
COMMAND_INVALID = 503

# The client attempted to work with a channel that had not been
# correctly
# opened. This most likely indicates a fault in the client layer.
CHANNEL_ERROR = 504

# The peer sent a frame that was not expected, usually in the context
# of
# a content header and body. This strongly indicates a fault in the
# peer's
# content processing.
UNEXPECTED_FRAME = 505

# The server could not complete the method because it lacked
# sufficient
# resources. This may be due to the client creating too many of some
# type
# of entity.
RESOURCE_ERROR = 506

# The client tried to work with some entity in a manner that is
# prohibited
# by the server, due to security settings or by some other criteria.
NOT_ALLOWED = 530

# The client tried to use functionality that is not implemented in the
# server.
NOT_IMPLEMENTED = 540

# The server could not complete the method because of an internal
# error.
# The server may require intervention by an operator in order to
# resume
# normal operations.
INTERNAL_ERROR = 541

SOFT_ERRORS = [
    CONTENT_TOO_LARGE, NO_CONSUMERS, ACCESS_REFUSED, NOT_FOUND,
    RESOURCE_LOCKED, PRECONDITION_FAILED
]
HARD_ERRORS = [
    CONNECTION_FORCED, INVALID_PATH, FRAME_ERROR, SYNTAX_ERROR,
    COMMAND_INVALID, CHANNEL_ERROR, UNEXPECTED_FRAME, RESOURCE_ERROR,
    NOT_ALLOWED, NOT_IMPLEMENTED, INTERNAL_ERROR
]

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


class Connection(AMQPClass):
    """
    The connection class provides methods for a client to establish a
    
    network connection to
    a server, and for both peers to operate the connection thereafter.
    """
    NAME = u'connection'
    INDEX = 10


class ConnectionBlocked(AMQPMethodPayload):
    """
    This method indicates that a connection has been blocked
    
    and does not accept new publishes.

    :type reason: binary type (max length 255) (shortstr in AMQP)
    """
    __slots__ = (u'reason',)

    NAME = u'connection.blocked'

    INDEX = (10, 60)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x3C'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reason', u'shortstr', u'shortstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionBlocked(%s)' % (', '.join(map(repr, [self.reason])))

    def __init__(self, reason):
        """
        Create frame connection.blocked
        """
        self.reason = reason

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack(len(self.reason)))
        buf.write(self.reason)

    def get_size(self):  # type: () -> int
        return 1 + len(self.reason)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionBlocked
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        reason = buf[offset:offset + s_len]
        offset += s_len
        return cls(reason)


class ConnectionClose(AMQPMethodPayload):
    """
    Request a connection close
    
    This method indicates that the sender wants to close the
    connection. This may be
    due to internal conditions (e.g. a forced shut-down) or due to
    an error handling
    a specific method, i.e. an exception. When a close is due to an
    exception, the
    sender provides the class and method id of the method which
    caused the exception.

    :type reply_code: int, 16 bit unsigned (reply-code in AMQP)
    :type reply_text: binary type (max length 255) (reply-text in AMQP)
    :param class_id: Failing method class
            When the close is provoked by a method exception, this is
            the class of the
            method.
    :type class_id: int, 16 bit unsigned (class-id in AMQP)
    :param method_id: Failing method id
            When the close is provoked by a method exception, this is
            the ID of the method.
    :type method_id: int, 16 bit unsigned (method-id in AMQP)
    """
    __slots__ = (
        u'reply_code',
        u'reply_text',
        u'class_id',
        u'method_id',
    )

    NAME = u'connection.close'

    INDEX = (10, 50)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x32'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reply-code', u'reply-code', u'short', reserved=False),
        Field(u'reply-text', u'reply-text', u'shortstr', reserved=False),
        Field(u'class-id', u'class-id', u'short', reserved=False),
        Field(u'method-id', u'method-id', u'short', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionClose(%s)' % (', '.join(
            map(repr, [
                self.reply_code, self.reply_text, self.class_id, self.method_id
            ])))

    def __init__(self, reply_code, reply_text, class_id, method_id):
        """
        Create frame connection.close
        """
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.class_id = class_id
        self.method_id = method_id

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_HB.pack(self.reply_code, len(self.reply_text)))
        buf.write(self.reply_text)
        buf.write(STRUCT_HH.pack(self.class_id, self.method_id))

    def get_size(self):  # type: () -> int
        return 7 + len(self.reply_text)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionClose
        offset = start_offset
        reply_code, s_len, = STRUCT_HB.unpack_from(buf, offset)
        offset += 3
        reply_text = buf[offset:offset + s_len]
        offset += s_len
        class_id, method_id, = STRUCT_HH.unpack_from(buf, offset)
        offset += 4
        return cls(reply_code, reply_text, class_id, method_id)


class ConnectionCloseOk(AMQPMethodPayload):
    """
    Confirm a connection close
    
    This method confirms a Connection.Close method and tells the
    recipient that it is
    safe to release resources for the connection and close the
    socket.

    """
    __slots__ = ()

    NAME = u'connection.close-ok'

    INDEX = (10, 51)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x33'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x0A\x00\x33\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionCloseOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionCloseOk
        offset = start_offset
        return cls()


class ConnectionOpen(AMQPMethodPayload):
    """
    Open connection to virtual host
    
    This method opens a connection to a virtual host, which is a
    collection of
    resources, and acts to separate multiple application domains
    within a server.
    The server may apply arbitrary limits per virtual host, such as
    the number
    of each type of entity that may be used, per connection and/or
    in total.

    :param virtual_host: Virtual host name
            The name of the virtual host to work with.
    :type virtual_host: binary type (max length 255) (path in AMQP)
    """
    __slots__ = (u'virtual_host',)

    NAME = u'connection.open'

    INDEX = (10, 40)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x28'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'virtual-host', u'path', u'shortstr', reserved=False),
        Field(u'reserved-1', u'shortstr', u'shortstr', reserved=True),
        Field(u'reserved-2', u'bit', u'bit', reserved=True),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionOpen(%s)' % (', '.join(map(repr,
                                                     [self.virtual_host])))

    def __init__(self, virtual_host):
        """
        Create frame connection.open
        """
        self.virtual_host = virtual_host

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack(len(self.virtual_host)))
        buf.write(self.virtual_host)
        buf.write(b'\x00')
        buf.write(STRUCT_B.pack(0))

    def get_size(self):  # type: () -> int
        return 3 + len(self.virtual_host)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionOpen
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        virtual_host = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        offset += s_len  # reserved field!
        offset += 1
        return cls(virtual_host)


class ConnectionOpenOk(AMQPMethodPayload):
    """
    Signal that connection is ready
    
    This method signals to the client that the connection is ready
    for use.

    """
    __slots__ = ()

    NAME = u'connection.open-ok'

    INDEX = (10, 41)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x29'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x0A\x00\x29\x00\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'shortstr', u'shortstr', reserved=True),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionOpenOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionOpenOk
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        offset += s_len  # reserved field!
        return cls()


class ConnectionStart(AMQPMethodPayload):
    """
    Start connection negotiation
    
    This method starts the connection negotiation process by telling
    the client the
    protocol version that the server proposes, along with a list of
    security mechanisms
    which the client can use for authentication.

    :param version_major: Protocol major version
            The major version number can take any value from 0 to 99 as
            defined in the
            AMQP specification.
    :type version_major: int, 8 bit unsigned (octet in AMQP)
    :param version_minor: Protocol minor version
            The minor version number can take any value from 0 to 99 as
            defined in the
            AMQP specification.
    :type version_minor: int, 8 bit unsigned (octet in AMQP)
    :param server_properties: Server properties
            The properties SHOULD contain at least these fields:
            "host", specifying the
            server host name or address, "product", giving the name
            of the server product,
            "version", giving the name of the server version,
            "platform", giving the name
            of the operating system, "copyright", if appropriate,
            and "information", giving
            other general information.
    :type server_properties: table. See coolamqp.uplink.framing.field_table (peer-properties in AMQP)
    :param mechanisms: Available security mechanisms
            A list of the security mechanisms that the server supports,
            delimited by spaces.
    :type mechanisms: binary type (longstr in AMQP)
    :param locales: Available message locales
            A list of the message locales that the server supports,
            delimited by spaces. The
            locale defines the language in which the server will send
            reply texts.
    :type locales: binary type (longstr in AMQP)
    """
    __slots__ = (
        u'version_major',
        u'version_minor',
        u'server_properties',
        u'mechanisms',
        u'locales',
    )

    NAME = u'connection.start'

    INDEX = (10, 10)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x0A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'version-major', u'octet', u'octet', reserved=False),
        Field(u'version-minor', u'octet', u'octet', reserved=False),
        Field(u'server-properties',
              u'peer-properties',
              u'table',
              reserved=False),
        Field(u'mechanisms', u'longstr', u'longstr', reserved=False),
        Field(u'locales', u'longstr', u'longstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionStart(%s)' % (', '.join(
            map(repr, [
                self.version_major, self.version_minor, self.server_properties,
                self.mechanisms, self.locales
            ])))

    def __init__(self, version_major, version_minor, server_properties,
                 mechanisms, locales):
        """
        Create frame connection.start
        """
        self.version_major = version_major
        self.version_minor = version_minor
        self.server_properties = server_properties
        self.mechanisms = mechanisms
        self.locales = locales

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_BB.pack(self.version_major, self.version_minor))
        enframe_table(buf, self.server_properties)
        buf.write(STRUCT_I.pack(len(self.mechanisms)))
        buf.write(self.mechanisms)
        buf.write(STRUCT_I.pack(len(self.locales)))
        buf.write(self.locales)

    def get_size(self):  # type: () -> int
        return 10 + frame_table_size(self.server_properties) + len(
            self.mechanisms) + len(self.locales)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionStart
        offset = start_offset
        version_major, version_minor, = STRUCT_BB.unpack_from(buf, offset)
        offset += 2
        server_properties, delta = deframe_table(buf, offset)
        offset += delta
        s_len, = STRUCT_L.unpack_from(buf, offset)
        offset += 4
        mechanisms = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_L.unpack_from(buf, offset)
        offset += 4
        locales = buf[offset:offset + s_len]
        offset += s_len
        return cls(version_major, version_minor, server_properties, mechanisms,
                   locales)


class ConnectionSecure(AMQPMethodPayload):
    """
    Security mechanism challenge
    
    The SASL protocol works by exchanging challenges and responses
    until both peers have
    received sufficient information to authenticate each other. This
    method challenges
    the client to provide more information.

    :param challenge: Security challenge data
            Challenge information, a block of opaque binary data passed
            to the security
            mechanism.
    :type challenge: binary type (longstr in AMQP)
    """
    __slots__ = (u'challenge',)

    NAME = u'connection.secure'

    INDEX = (10, 20)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x14'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'challenge', u'longstr', u'longstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionSecure(%s)' % (', '.join(map(repr,
                                                       [self.challenge])))

    def __init__(self, challenge):
        """
        Create frame connection.secure
        """
        self.challenge = challenge

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_I.pack(len(self.challenge)))
        buf.write(self.challenge)

    def get_size(self):  # type: () -> int
        return 4 + len(self.challenge)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionSecure
        offset = start_offset
        s_len, = STRUCT_L.unpack_from(buf, offset)
        offset += 4
        challenge = buf[offset:offset + s_len]
        offset += s_len
        return cls(challenge)


class ConnectionStartOk(AMQPMethodPayload):
    """
    Select security mechanism and locale
    
    This method selects a SASL security mechanism.

    :param client_properties: Client properties
            The properties SHOULD contain at least these fields:
            "product", giving the name
            of the client product, "version", giving the name of the
            client version, "platform",
            giving the name of the operating system, "copyright", if
            appropriate, and
            "information", giving other general information.
    :type client_properties: table. See coolamqp.uplink.framing.field_table (peer-properties in AMQP)
    :param mechanism: Selected security mechanism
            A single security mechanisms selected by the client, which
            must be one of those
            specified by the server.
    :type mechanism: binary type (max length 255) (shortstr in AMQP)
    :param response: Security response data
            A block of opaque data passed to the security mechanism. The
            contents of this
            data are defined by the SASL security mechanism.
    :type response: binary type (longstr in AMQP)
    :param locale: Selected message locale
            A single message locale selected by the client, which must
            be one of those
            specified by the server.
    :type locale: binary type (max length 255) (shortstr in AMQP)
    """
    __slots__ = (
        u'client_properties',
        u'mechanism',
        u'response',
        u'locale',
    )

    NAME = u'connection.start-ok'

    INDEX = (10, 11)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x0B'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'client-properties',
              u'peer-properties',
              u'table',
              reserved=False),
        Field(u'mechanism', u'shortstr', u'shortstr', reserved=False),
        Field(u'response', u'longstr', u'longstr', reserved=False),
        Field(u'locale', u'shortstr', u'shortstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionStartOk(%s)' % (', '.join(
            map(repr, [
                self.client_properties, self.mechanism, self.response,
                self.locale
            ])))

    def __init__(self, client_properties, mechanism, response, locale):
        """
        Create frame connection.start-ok
        """
        self.client_properties = client_properties
        self.mechanism = mechanism
        self.response = response
        self.locale = locale

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        enframe_table(buf, self.client_properties)
        buf.write(STRUCT_B.pack(len(self.mechanism)))
        buf.write(self.mechanism)
        buf.write(STRUCT_I.pack(len(self.response)))
        buf.write(self.response)
        buf.write(STRUCT_B.pack(len(self.locale)))
        buf.write(self.locale)

    def get_size(self):  # type: () -> int
        return 6 + frame_table_size(self.client_properties) + len(
            self.mechanism) + len(self.response) + len(self.locale)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionStartOk
        offset = start_offset
        client_properties, delta = deframe_table(buf, offset)
        offset += delta
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        mechanism = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_L.unpack_from(buf, offset)
        offset += 4
        response = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        locale = buf[offset:offset + s_len]
        offset += s_len
        return cls(client_properties, mechanism, response, locale)


class ConnectionSecureOk(AMQPMethodPayload):
    """
    Security mechanism response
    
    This method attempts to authenticate, passing a block of SASL
    data for the security
    mechanism at the server side.

    :param response: Security response data
            A block of opaque data passed to the security mechanism. The
            contents of this
            data are defined by the SASL security mechanism.
    :type response: binary type (longstr in AMQP)
    """
    __slots__ = (u'response',)

    NAME = u'connection.secure-ok'

    INDEX = (10, 21)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x15'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'response', u'longstr', u'longstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionSecureOk(%s)' % (', '.join(map(
            repr, [self.response])))

    def __init__(self, response):
        """
        Create frame connection.secure-ok
        """
        self.response = response

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_I.pack(len(self.response)))
        buf.write(self.response)

    def get_size(self):  # type: () -> int
        return 4 + len(self.response)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionSecureOk
        offset = start_offset
        s_len, = STRUCT_L.unpack_from(buf, offset)
        offset += 4
        response = buf[offset:offset + s_len]
        offset += s_len
        return cls(response)


class ConnectionTune(AMQPMethodPayload):
    """
    Propose connection tuning parameters
    
    This method proposes a set of connection configuration values to
    the client. The
    client can accept and/or adjust these.

    :param channel_max: Proposed maximum channels
            Specifies highest channel number that the server permits.
            Usable channel numbers
            are in the range 1..channel-max. Zero indicates no specified
            limit.
    :type channel_max: int, 16 bit unsigned (short in AMQP)
    :param frame_max: Proposed maximum frame size
            The largest frame size that the server proposes for the
            connection, including
            frame header and end-byte. The client can negotiate a lower
            value. Zero means
            that the server does not impose any specific limit but may
            reject very large
            frames if it cannot allocate resources for them.
    :type frame_max: int, 32 bit unsigned (long in AMQP)
    :param heartbeat: Desired heartbeat delay
            The delay, in seconds, of the connection heartbeat that the
            server wants.
            Zero means the server does not want a heartbeat.
    :type heartbeat: int, 16 bit unsigned (short in AMQP)
    """
    __slots__ = (
        u'channel_max',
        u'frame_max',
        u'heartbeat',
    )

    NAME = u'connection.tune'

    INDEX = (10, 30)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x1E'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'channel-max', u'short', u'short', reserved=False),
        Field(u'frame-max', u'long', u'long', reserved=False),
        Field(u'heartbeat', u'short', u'short', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionTune(%s)' % (', '.join(
            map(repr, [self.channel_max, self.frame_max, self.heartbeat])))

    def __init__(self, channel_max, frame_max, heartbeat):
        """
        Create frame connection.tune
        """
        self.channel_max = channel_max
        self.frame_max = frame_max
        self.heartbeat = heartbeat

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(
            STRUCT_HIH.pack(self.channel_max, self.frame_max, self.heartbeat))

    def get_size(self):  # type: () -> int
        return 8

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionTune
        offset = start_offset
        channel_max, frame_max, heartbeat, = STRUCT_HIH.unpack_from(
            buf, offset)
        offset += 8
        return cls(channel_max, frame_max, heartbeat)


class ConnectionTuneOk(AMQPMethodPayload):
    """
    Negotiate connection tuning parameters
    
    This method sends the client's connection tuning parameters to
    the server.
    Certain fields are negotiated, others provide capability
    information.

    :param channel_max: Negotiated maximum channels
            The maximum total number of channels that the client will
            use per connection.
    :type channel_max: int, 16 bit unsigned (short in AMQP)
    :param frame_max: Negotiated maximum frame size
            The largest frame size that the client and server will use
            for the connection.
            Zero means that the client does not impose any specific
            limit but may reject
            very large frames if it cannot allocate resources for them.
            Note that the
            frame-max limit applies principally to content frames, where
            large contents can
            be broken into frames of arbitrary size.
    :type frame_max: int, 32 bit unsigned (long in AMQP)
    :param heartbeat: Desired heartbeat delay
            The delay, in seconds, of the connection heartbeat that the
            client wants. Zero
            means the client does not want a heartbeat.
    :type heartbeat: int, 16 bit unsigned (short in AMQP)
    """
    __slots__ = (
        u'channel_max',
        u'frame_max',
        u'heartbeat',
    )

    NAME = u'connection.tune-ok'

    INDEX = (10, 31)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x1F'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'channel-max', u'short', u'short', reserved=False),
        Field(u'frame-max', u'long', u'long', reserved=False),
        Field(u'heartbeat', u'short', u'short', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionTuneOk(%s)' % (', '.join(
            map(repr, [self.channel_max, self.frame_max, self.heartbeat])))

    def __init__(self, channel_max, frame_max, heartbeat):
        """
        Create frame connection.tune-ok
        """
        self.channel_max = channel_max
        self.frame_max = frame_max
        self.heartbeat = heartbeat

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(
            STRUCT_HIH.pack(self.channel_max, self.frame_max, self.heartbeat))

    def get_size(self):  # type: () -> int
        return 8

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConnectionTuneOk
        offset = start_offset
        channel_max, frame_max, heartbeat, = STRUCT_HIH.unpack_from(
            buf, offset)
        offset += 8
        return cls(channel_max, frame_max, heartbeat)


class ConnectionUnblocked(AMQPMethodPayload):
    """
    This method indicates that a connection has been unblocked
    
    and now accepts publishes.

    """
    __slots__ = ()

    NAME = u'connection.unblocked'

    INDEX = (10, 61)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x0A\x00\x3D'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x0A\x00\x3D\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConnectionUnblocked(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(
            cls, buf, start_offset):  # type: (buffer, int) -> ConnectionUnblocked
        offset = start_offset
        return cls()


class Channel(AMQPClass):
    """
    The channel class provides methods for a client to establish a
    
    channel to a
    server and for both peers to operate the channel thereafter.
    """
    NAME = u'channel'
    INDEX = 20


class ChannelClose(AMQPMethodPayload):
    """
    Request a channel close
    
    This method indicates that the sender wants to close the
    channel. This may be due to
    internal conditions (e.g. a forced shut-down) or due to an error
    handling a specific
    method, i.e. an exception. When a close is due to an exception,
    the sender provides
    the class and method id of the method which caused the
    exception.

    :type reply_code: int, 16 bit unsigned (reply-code in AMQP)
    :type reply_text: binary type (max length 255) (reply-text in AMQP)
    :param class_id: Failing method class
            When the close is provoked by a method exception, this is
            the class of the
            method.
    :type class_id: int, 16 bit unsigned (class-id in AMQP)
    :param method_id: Failing method id
            When the close is provoked by a method exception, this is
            the ID of the method.
    :type method_id: int, 16 bit unsigned (method-id in AMQP)
    """
    __slots__ = (
        u'reply_code',
        u'reply_text',
        u'class_id',
        u'method_id',
    )

    NAME = u'channel.close'

    INDEX = (20, 40)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x14\x00\x28'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reply-code', u'reply-code', u'short', reserved=False),
        Field(u'reply-text', u'reply-text', u'shortstr', reserved=False),
        Field(u'class-id', u'class-id', u'short', reserved=False),
        Field(u'method-id', u'method-id', u'short', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ChannelClose(%s)' % (', '.join(
            map(repr, [
                self.reply_code, self.reply_text, self.class_id, self.method_id
            ])))

    def __init__(self, reply_code, reply_text, class_id, method_id):
        """
        Create frame channel.close
        """
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.class_id = class_id
        self.method_id = method_id

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_HB.pack(self.reply_code, len(self.reply_text)))
        buf.write(self.reply_text)
        buf.write(STRUCT_HH.pack(self.class_id, self.method_id))

    def get_size(self):  # type: () -> int
        return 7 + len(self.reply_text)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ChannelClose
        offset = start_offset
        reply_code, s_len, = STRUCT_HB.unpack_from(buf, offset)
        offset += 3
        reply_text = buf[offset:offset + s_len]
        offset += s_len
        class_id, method_id, = STRUCT_HH.unpack_from(buf, offset)
        offset += 4
        return cls(reply_code, reply_text, class_id, method_id)


class ChannelCloseOk(AMQPMethodPayload):
    """
    Confirm a channel close
    
    This method confirms a Channel.Close method and tells the
    recipient that it is safe
    to release resources for the channel.

    """
    __slots__ = ()

    NAME = u'channel.close-ok'

    INDEX = (20, 41)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x14\x00\x29'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x14\x00\x29\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ChannelCloseOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ChannelCloseOk
        offset = start_offset
        return cls()


class ChannelFlow(AMQPMethodPayload):
    """
    Enable/disable flow from peer
    
    This method asks the peer to pause or restart the flow of
    content data sent by
    a consumer. This is a simple flow-control mechanism that a peer
    can use to avoid
    overflowing its queues or otherwise finding itself receiving
    more messages than
    it can process. Note that this method is not intended for window
    control. It does
    not affect contents returned by Basic.Get-Ok methods.

    :param active: Start/stop content frames
            If 1, the peer starts sending content frames. If 0, the peer
            stops sending
            content frames.
    :type active: bool (bit in AMQP)
    """
    __slots__ = (u'active',)

    NAME = u'channel.flow'

    INDEX = (20, 20)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x14\x00\x14'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'active', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ChannelFlow(%s)' % (', '.join(map(repr, [self.active])))

    def __init__(self, active):
        """
        Create frame channel.flow
        """
        self.active = active

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack((self.active << 0)))

    def get_size(self):  # type: () -> int
        return 1

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ChannelFlow
        offset = start_offset
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        active = bool(_bit >> 0)
        offset += 1
        return cls(active)


class ChannelFlowOk(AMQPMethodPayload):
    """
    Confirm a flow method
    
    Confirms to the peer that a flow command was received and
    processed.

    :param active: Current flow setting
            Confirms the setting of the processed flow method: 1 means
            the peer will start
            sending or continue to send content frames; 0 means it will
            not.
    :type active: bool (bit in AMQP)
    """
    __slots__ = (u'active',)

    NAME = u'channel.flow-ok'

    INDEX = (20, 21)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x14\x00\x15'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'active', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ChannelFlowOk(%s)' % (', '.join(map(repr, [self.active])))

    def __init__(self, active):
        """
        Create frame channel.flow-ok
        """
        self.active = active

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack((self.active << 0)))

    def get_size(self):  # type: () -> int
        return 1

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ChannelFlowOk
        offset = start_offset
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        active = bool(_bit >> 0)
        offset += 1
        return cls(active)


class ChannelOpen(AMQPMethodPayload):
    """
    Open a channel for use
    
    This method opens a channel to the server.

    """
    __slots__ = ()

    NAME = u'channel.open'

    INDEX = (20, 10)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x14\x00\x0A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x05\x00\x14\x00\x0A\x00\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'shortstr', u'shortstr', reserved=True),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ChannelOpen(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ChannelOpen
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        offset += s_len  # reserved field!
        return cls()


class ChannelOpenOk(AMQPMethodPayload):
    """
    Signal that the channel is ready
    
    This method signals to the client that the channel is ready for
    use.

    """
    __slots__ = ()

    NAME = u'channel.open-ok'

    INDEX = (20, 11)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x14\x00\x0B'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x05\x00\x14\x00\x0B\x00\x00\x00\x00\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'longstr', u'longstr', reserved=True),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ChannelOpenOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ChannelOpenOk
        offset = start_offset
        s_len, = STRUCT_L.unpack_from(buf, offset)
        offset += 4
        offset += s_len  # reserved field!
        return cls()


class Exchange(AMQPClass):
    """
    Exchanges match and distribute messages across queues. exchanges can
    
    be configured in
    the server or declared at runtime.
    """
    NAME = u'exchange'
    INDEX = 40


class ExchangeBind(AMQPMethodPayload):
    """
    Bind exchange to an exchange
    
    This method binds an exchange to an exchange.

    :param destination: Name of the destination exchange to bind to
            Specifies the name of the destination exchange to bind.
    :type destination: binary type (max length 255) (exchange-name in AMQP)
    :param source: Name of the source exchange to bind to
            Specifies the name of the source exchange to bind.
    :type source: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Message routing key
            Specifies the routing key for the binding. The routing key
            is used for routing messages depending on the exchange
            configuration. Not all exchanges use a routing key - refer
            to the specific exchange documentation.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    :param arguments: Arguments for binding
            A set of arguments for the binding. The syntax and semantics
            of these arguments depends on the exchange class.
    :type arguments: table. See coolamqp.uplink.framing.field_table (table in AMQP)
    """
    __slots__ = (
        u'destination',
        u'source',
        u'routing_key',
        u'no_wait',
        u'arguments',
    )

    NAME = u'exchange.bind'

    INDEX = (40, 30)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x1E'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'destination', u'exchange-name', u'shortstr', reserved=False),
        Field(u'source', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
        Field(u'arguments', u'table', u'table', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeBind(%s)' % (', '.join(
            map(repr, [
                self.destination, self.source, self.routing_key, self.no_wait,
                self.arguments
            ])))

    def __init__(self, destination, source, routing_key, no_wait, arguments):
        """
        Create frame exchange.bind
        """
        self.destination = destination
        self.source = source
        self.routing_key = routing_key
        self.no_wait = no_wait
        self.arguments = arguments

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.destination)))
        buf.write(self.destination)
        buf.write(STRUCT_B.pack(len(self.source)))
        buf.write(self.source)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)
        buf.write(STRUCT_B.pack((self.no_wait << 0)))
        enframe_table(buf, self.arguments)

    def get_size(self):  # type: () -> int
        return 6 + len(self.destination) + len(self.source) + len(
            self.routing_key) + frame_table_size(self.arguments)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeBind
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        destination = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        source = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        no_wait = bool(_bit >> 0)
        offset += 1
        arguments, delta = deframe_table(buf, offset)
        offset += delta
        return cls(destination, source, routing_key, no_wait, arguments)


class ExchangeBindOk(AMQPMethodPayload):
    """
    Confirm bind successful
    
    This method confirms that the bind was successful.

    """
    __slots__ = ()

    NAME = u'exchange.bind-ok'

    INDEX = (40, 31)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x1F'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x28\x00\x1F\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeBindOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeBindOk
        offset = start_offset
        return cls()


class ExchangeDeclare(AMQPMethodPayload):
    """
    Verify exchange exists, create if needed
    
    This method creates an exchange if it does not already exist,
    and if the exchange
    exists, verifies that it is of the correct and expected class.

    :param exchange: Exchange names starting with "amq." are reserved for
            pre-declared and
            standardised exchanges. The client MAY declare an
            exchange starting with
            "amq." if the passive option is set, or the exchange
            already exists.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param type_: Exchange type
            Each exchange belongs to one of a set of exchange types
            implemented by the
            server. The exchange types define the functionality of the
            exchange - i.e. how
            messages are routed through it. It is not valid or
            meaningful to attempt to
            change the type of an existing exchange.
    :type type_: binary type (max length 255) (shortstr in AMQP)
    :param passive: Do not create exchange
            If set, the server will reply with Declare-Ok if the
            exchange already
            exists with the same name, and raise an error if not. The
            client can
            use this to check whether an exchange exists without
            modifying the
            server state. When set, all other method fields except name
            and no-wait
            are ignored. A declare with both passive and no-wait has no
            effect.
            Arguments are compared for semantic equivalence.
    :type passive: bool (bit in AMQP)
    :param durable: Request a durable exchange
            If set when creating a new exchange, the exchange will be
            marked as durable.
            Durable exchanges remain active when a server restarts.
            Non-durable exchanges
            (transient exchanges) are purged if/when a server restarts.
    :type durable: bool (bit in AMQP)
    :param auto_delete: Auto-delete when unused
            If set, the exchange is deleted when all queues have
            finished using it.
    :type auto_delete: bool (bit in AMQP)
    :param internal: Create internal exchange
            If set, the exchange may not be used directly by publishers,
            but only when bound to other exchanges. Internal exchanges
            are used to construct wiring that is not visible to
            applications.
    :type internal: bool (bit in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    :param arguments: Arguments for declaration
            A set of arguments for the declaration. The syntax and
            semantics of these
            arguments depends on the server implementation.
    :type arguments: table. See coolamqp.uplink.framing.field_table (table in AMQP)
    """
    __slots__ = (
        u'exchange',
        u'type_',
        u'passive',
        u'durable',
        u'auto_delete',
        u'internal',
        u'no_wait',
        u'arguments',
    )

    NAME = u'exchange.declare'

    INDEX = (40, 10)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x0A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'type', u'shortstr', u'shortstr', reserved=False),
        Field(u'passive', u'bit', u'bit', reserved=False),
        Field(u'durable', u'bit', u'bit', reserved=False),
        Field(u'auto-delete', u'bit', u'bit', reserved=False),
        Field(u'internal', u'bit', u'bit', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
        Field(u'arguments', u'table', u'table', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeDeclare(%s)' % (', '.join(
            map(repr, [
                self.exchange, self.type_, self.passive, self.durable,
                self.auto_delete, self.internal, self.no_wait, self.arguments
            ])))

    def __init__(self, exchange, type_, passive, durable, auto_delete,
                 internal, no_wait, arguments):
        """
        Create frame exchange.declare
        """
        self.exchange = exchange
        self.type_ = type_
        self.passive = passive
        self.durable = durable
        self.auto_delete = auto_delete
        self.internal = internal
        self.no_wait = no_wait
        self.arguments = arguments

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack(len(self.type_)))
        buf.write(self.type_)
        buf.write(
            STRUCT_B.pack((self.passive << 0) | (self.durable << 1)
                          | (self.auto_delete << 2) | (self.internal << 3)
                          | (self.no_wait << 4)))
        enframe_table(buf, self.arguments)

    def get_size(self):  # type: () -> int
        return 5 + len(self.exchange) + len(self.type_) + frame_table_size(
            self.arguments)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeDeclare
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        exchange = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        type_ = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        passive = bool(_bit >> 0)
        durable = bool(_bit >> 1)
        auto_delete = bool(_bit >> 2)
        internal = bool(_bit >> 3)
        no_wait = bool(_bit >> 4)
        offset += 1
        arguments, delta = deframe_table(buf, offset)
        offset += delta
        return cls(exchange, type_, passive, durable, auto_delete, internal,
                   no_wait, arguments)


class ExchangeDelete(AMQPMethodPayload):
    """
    Delete an exchange
    
    This method deletes an exchange. When an exchange is deleted all
    queue bindings on
    the exchange are cancelled.

    :param exchange: The client must not attempt to delete an exchange that
            does not exist.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param if_unused: Delete only if unused
            If set, the server will only delete the exchange if it has
            no queue bindings. If
            the exchange has queue bindings the server does not delete
            it but raises a
            channel exception instead.
    :type if_unused: bool (bit in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    """
    __slots__ = (
        u'exchange',
        u'if_unused',
        u'no_wait',
    )

    NAME = u'exchange.delete'

    INDEX = (40, 20)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x14'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'if-unused', u'bit', u'bit', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeDelete(%s)' % (', '.join(
            map(repr, [self.exchange, self.if_unused, self.no_wait])))

    def __init__(self, exchange, if_unused, no_wait):
        """
        Create frame exchange.delete
        """
        self.exchange = exchange
        self.if_unused = if_unused
        self.no_wait = no_wait

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack((self.if_unused << 0) | (self.no_wait << 1)))

    def get_size(self):  # type: () -> int
        return 4 + len(self.exchange)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeDelete
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        exchange = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        if_unused = bool(_bit >> 0)
        no_wait = bool(_bit >> 1)
        offset += 1
        return cls(exchange, if_unused, no_wait)


class ExchangeDeclareOk(AMQPMethodPayload):
    """
    Confirm exchange declaration
    
    This method confirms a Declare method and confirms the name of
    the exchange,
    essential for automatically-named exchanges.

    """
    __slots__ = ()

    NAME = u'exchange.declare-ok'

    INDEX = (40, 11)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x0B'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x28\x00\x0B\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeDeclareOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeDeclareOk
        offset = start_offset
        return cls()


class ExchangeDeleteOk(AMQPMethodPayload):
    """
    Confirm deletion of an exchange
    
    This method confirms the deletion of an exchange.

    """
    __slots__ = ()

    NAME = u'exchange.delete-ok'

    INDEX = (40, 21)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x15'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x28\x00\x15\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeDeleteOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeDeleteOk
        offset = start_offset
        return cls()


class ExchangeUnbind(AMQPMethodPayload):
    """
    Unbind an exchange from an exchange
    
    This method unbinds an exchange from an exchange.

    :param destination: Specifies the name of the destination exchange to unbind.
    :type destination: binary type (max length 255) (exchange-name in AMQP)
    :param source: Specifies the name of the source exchange to unbind.
    :type source: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Routing key of binding
            Specifies the routing key of the binding to unbind.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    :param arguments: Arguments of binding
            Specifies the arguments of the binding to unbind.
    :type arguments: table. See coolamqp.uplink.framing.field_table (table in AMQP)
    """
    __slots__ = (
        u'destination',
        u'source',
        u'routing_key',
        u'no_wait',
        u'arguments',
    )

    NAME = u'exchange.unbind'

    INDEX = (40, 40)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x28'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'destination', u'exchange-name', u'shortstr', reserved=False),
        Field(u'source', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
        Field(u'arguments', u'table', u'table', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeUnbind(%s)' % (', '.join(
            map(repr, [
                self.destination, self.source, self.routing_key, self.no_wait,
                self.arguments
            ])))

    def __init__(self, destination, source, routing_key, no_wait, arguments):
        """
        Create frame exchange.unbind
        """
        self.destination = destination
        self.source = source
        self.routing_key = routing_key
        self.no_wait = no_wait
        self.arguments = arguments

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.destination)))
        buf.write(self.destination)
        buf.write(STRUCT_B.pack(len(self.source)))
        buf.write(self.source)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)
        buf.write(STRUCT_B.pack((self.no_wait << 0)))
        enframe_table(buf, self.arguments)

    def get_size(self):  # type: () -> int
        return 6 + len(self.destination) + len(self.source) + len(
            self.routing_key) + frame_table_size(self.arguments)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeUnbind
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        destination = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        source = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        no_wait = bool(_bit >> 0)
        offset += 1
        arguments, delta = deframe_table(buf, offset)
        offset += delta
        return cls(destination, source, routing_key, no_wait, arguments)


class ExchangeUnbindOk(AMQPMethodPayload):
    """
    Confirm unbind successful
    
    This method confirms that the unbind was successful.

    """
    __slots__ = ()

    NAME = u'exchange.unbind-ok'

    INDEX = (40, 51)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x28\x00\x33'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x28\x00\x33\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ExchangeUnbindOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ExchangeUnbindOk
        offset = start_offset
        return cls()


class Queue(AMQPClass):
    """
    Queues store and forward messages. queues can be configured in the
    
    server or created at
    runtime. Queues must be attached to at least one exchange in order
    to receive messages
    from publishers.
    """
    NAME = u'queue'
    INDEX = 50


class QueueBind(AMQPMethodPayload):
    """
    Bind queue to an exchange
    
    This method binds a queue to an exchange. Until a queue is bound
    it will not
    receive any messages. In a classic messaging model,
    store-and-forward queues
    are bound to a direct exchange and subscription queues are bound
    to a topic
    exchange.

    :param queue: Specifies the name of the queue to bind.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :param exchange: Name of the exchange to bind to
            A client MUST NOT be allowed to bind a queue to a
            non-existent exchange.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Message routing key
            Specifies the routing key for the binding. The routing key
            is used for routing
            messages depending on the exchange configuration. Not all
            exchanges use a
            routing key - refer to the specific exchange documentation.
            If the queue name
            is empty, the server uses the last queue declared on the
            channel. If the
            routing key is also empty, the server uses this queue name
            for the routing
            key as well. If the queue name is provided but the routing
            key is empty, the
            server does the binding with that empty routing key. The
            meaning of empty
            routing keys depends on the exchange implementation.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    :param arguments: Arguments for binding
            A set of arguments for the binding. The syntax and semantics
            of these arguments
            depends on the exchange class.
    :type arguments: table. See coolamqp.uplink.framing.field_table (table in AMQP)
    """
    __slots__ = (
        u'queue',
        u'exchange',
        u'routing_key',
        u'no_wait',
        u'arguments',
    )

    NAME = u'queue.bind'

    INDEX = (50, 20)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x14'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
        Field(u'arguments', u'table', u'table', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueBind(%s)' % (', '.join(
            map(repr, [
                self.queue, self.exchange, self.routing_key, self.no_wait,
                self.arguments
            ])))

    def __init__(self, queue, exchange, routing_key, no_wait, arguments):
        """
        Create frame queue.bind
        """
        self.queue = queue
        self.exchange = exchange
        self.routing_key = routing_key
        self.no_wait = no_wait
        self.arguments = arguments

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(STRUCT_B.pack(len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)
        buf.write(STRUCT_B.pack((self.no_wait << 0)))
        enframe_table(buf, self.arguments)

    def get_size(self):  # type: () -> int
        return 6 + len(self.queue) + len(self.exchange) + len(
            self.routing_key) + frame_table_size(self.arguments)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueBind
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        queue = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        exchange = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        no_wait = bool(_bit >> 0)
        offset += 1
        arguments, delta = deframe_table(buf, offset)
        offset += delta
        return cls(queue, exchange, routing_key, no_wait, arguments)


class QueueBindOk(AMQPMethodPayload):
    """
    Confirm bind successful
    
    This method confirms that the bind was successful.

    """
    __slots__ = ()

    NAME = u'queue.bind-ok'

    INDEX = (50, 21)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x15'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x32\x00\x15\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueBindOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueBindOk
        offset = start_offset
        return cls()


class QueueDeclare(AMQPMethodPayload):
    """
    Declare queue, create if needed
    
    This method creates or checks a queue. When creating a new queue
    the client can
    specify various properties that control the durability of the
    queue and its
    contents, and the level of sharing for the queue.

    :param queue: The queue name may be empty, in which case the server
            MUST create a new
            queue with a unique generated name and return this to
            the client in the
            Declare-Ok method.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :param passive: Do not create queue
            If set, the server will reply with Declare-Ok if the queue
            already
            exists with the same name, and raise an error if not. The
            client can
            use this to check whether a queue exists without modifying
            the
            server state. When set, all other method fields except name
            and no-wait
            are ignored. A declare with both passive and no-wait has no
            effect.
            Arguments are compared for semantic equivalence.
    :type passive: bool (bit in AMQP)
    :param durable: Request a durable queue
            If set when creating a new queue, the queue will be marked
            as durable. Durable
            queues remain active when a server restarts. Non-durable
            queues (transient
            queues) are purged if/when a server restarts. Note that
            durable queues do not
            necessarily hold persistent messages, although it does not
            make sense to send
            persistent messages to a transient queue.
    :type durable: bool (bit in AMQP)
    :param exclusive: Request an exclusive queue
            Exclusive queues may only be accessed by the current
            connection, and are
            deleted when that connection closes. Passive declaration of
            an exclusive
            queue by other connections are not allowed.
    :type exclusive: bool (bit in AMQP)
    :param auto_delete: Auto-delete queue when unused
            If set, the queue is deleted when all consumers have
            finished using it. The last
            consumer can be cancelled either explicitly or because its
            channel is closed. If
            there was no consumer ever on the queue, it won't be
            deleted. Applications can
            explicitly delete auto-delete queues using the Delete method
            as normal.
    :type auto_delete: bool (bit in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    :param arguments: Arguments for declaration
            A set of arguments for the declaration. The syntax and
            semantics of these
            arguments depends on the server implementation.
    :type arguments: table. See coolamqp.uplink.framing.field_table (table in AMQP)
    """
    __slots__ = (
        u'queue',
        u'passive',
        u'durable',
        u'exclusive',
        u'auto_delete',
        u'no_wait',
        u'arguments',
    )

    NAME = u'queue.declare'

    INDEX = (50, 10)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x0A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'passive', u'bit', u'bit', reserved=False),
        Field(u'durable', u'bit', u'bit', reserved=False),
        Field(u'exclusive', u'bit', u'bit', reserved=False),
        Field(u'auto-delete', u'bit', u'bit', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
        Field(u'arguments', u'table', u'table', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueDeclare(%s)' % (', '.join(
            map(repr, [
                self.queue, self.passive, self.durable, self.exclusive,
                self.auto_delete, self.no_wait, self.arguments
            ])))

    def __init__(self, queue, passive, durable, exclusive, auto_delete,
                 no_wait, arguments):
        """
        Create frame queue.declare
        """
        self.queue = queue
        self.passive = passive
        self.durable = durable
        self.exclusive = exclusive
        self.auto_delete = auto_delete
        self.no_wait = no_wait
        self.arguments = arguments

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(
            STRUCT_B.pack((self.passive << 0) | (self.durable << 1)
                          | (self.exclusive << 2) | (self.auto_delete << 3)
                          | (self.no_wait << 4)))
        enframe_table(buf, self.arguments)

    def get_size(self):  # type: () -> int
        return 4 + len(self.queue) + frame_table_size(self.arguments)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueDeclare
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        queue = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        passive = bool(_bit >> 0)
        durable = bool(_bit >> 1)
        exclusive = bool(_bit >> 2)
        auto_delete = bool(_bit >> 3)
        no_wait = bool(_bit >> 4)
        offset += 1
        arguments, delta = deframe_table(buf, offset)
        offset += delta
        return cls(queue, passive, durable, exclusive, auto_delete, no_wait,
                   arguments)


class QueueDelete(AMQPMethodPayload):
    """
    Delete a queue
    
    This method deletes a queue. When a queue is deleted any pending
    messages are sent
    to a dead-letter queue if this is defined in the server
    configuration, and all
    consumers on the queue are cancelled.

    :param queue: Specifies the name of the queue to delete.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :param if_unused: Delete only if unused
            If set, the server will only delete the queue if it has no
            consumers. If the
            queue has consumers the server does does not delete it but
            raises a channel
            exception instead.
    :type if_unused: bool (bit in AMQP)
    :param if_empty: Delete only if empty
            If set, the server will only delete the queue if it has no
            messages.
    :type if_empty: bool (bit in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    """
    __slots__ = (
        u'queue',
        u'if_unused',
        u'if_empty',
        u'no_wait',
    )

    NAME = u'queue.delete'

    INDEX = (50, 40)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x28'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'if-unused', u'bit', u'bit', reserved=False),
        Field(u'if-empty', u'bit', u'bit', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueDelete(%s)' % (', '.join(
            map(repr,
                [self.queue, self.if_unused, self.if_empty, self.no_wait])))

    def __init__(self, queue, if_unused, if_empty, no_wait):
        """
        Create frame queue.delete
        """
        self.queue = queue
        self.if_unused = if_unused
        self.if_empty = if_empty
        self.no_wait = no_wait

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(
            STRUCT_B.pack((self.if_unused << 0) | (self.if_empty << 1)
                          | (self.no_wait << 2)))

    def get_size(self):  # type: () -> int
        return 4 + len(self.queue)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueDelete
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        queue = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        if_unused = bool(_bit >> 0)
        if_empty = bool(_bit >> 1)
        no_wait = bool(_bit >> 2)
        offset += 1
        return cls(queue, if_unused, if_empty, no_wait)


class QueueDeclareOk(AMQPMethodPayload):
    """
    Confirms a queue definition
    
    This method confirms a Declare method and confirms the name of
    the queue, essential
    for automatically-named queues.

    :param queue: Reports the name of the queue. if the server generated a
            queue name, this field
            contains that name.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :type message_count: int, 32 bit unsigned (message-count in AMQP)
    :param consumer_count: Number of consumers
            Reports the number of active consumers for the queue. Note
            that consumers can
            suspend activity (Channel.Flow) in which case they do not
            appear in this count.
    :type consumer_count: int, 32 bit unsigned (long in AMQP)
    """
    __slots__ = (
        u'queue',
        u'message_count',
        u'consumer_count',
    )

    NAME = u'queue.declare-ok'

    INDEX = (50, 11)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x0B'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'message-count', u'message-count', u'long', reserved=False),
        Field(u'consumer-count', u'long', u'long', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueDeclareOk(%s)' % (', '.join(
            map(repr, [self.queue, self.message_count, self.consumer_count])))

    def __init__(self, queue, message_count, consumer_count):
        """
        Create frame queue.declare-ok
        """
        self.queue = queue
        self.message_count = message_count
        self.consumer_count = consumer_count

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(STRUCT_II.pack(self.message_count, self.consumer_count))

    def get_size(self):  # type: () -> int
        return 9 + len(self.queue)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueDeclareOk
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        queue = buf[offset:offset + s_len]
        offset += s_len
        message_count, consumer_count, = STRUCT_II.unpack_from(buf, offset)
        offset += 8
        return cls(queue, message_count, consumer_count)


class QueueDeleteOk(AMQPMethodPayload):
    """
    Confirm deletion of a queue
    
    This method confirms the deletion of a queue.

    :param message_count: Reports the number of messages deleted.
    :type message_count: int, 32 bit unsigned (message-count in AMQP)
    """
    __slots__ = (u'message_count',)

    NAME = u'queue.delete-ok'

    INDEX = (50, 41)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x29'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'message-count', u'message-count', u'long', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueDeleteOk(%s)' % (', '.join(map(repr,
                                                    [self.message_count])))

    def __init__(self, message_count):
        """
        Create frame queue.delete-ok
        """
        self.message_count = message_count

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_I.pack(self.message_count))

    def get_size(self):  # type: () -> int
        return 4

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueDeleteOk
        offset = start_offset
        message_count, = STRUCT_I.unpack_from(buf, offset)
        offset += 4
        return cls(message_count)


class QueuePurge(AMQPMethodPayload):
    """
    Purge a queue
    
    This method removes all messages from a queue which are not
    awaiting
    acknowledgment.

    :param queue: Specifies the name of the queue to purge.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    """
    __slots__ = (
        u'queue',
        u'no_wait',
    )

    NAME = u'queue.purge'

    INDEX = (50, 30)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x1E'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueuePurge(%s)' % (', '.join(
            map(repr, [self.queue, self.no_wait])))

    def __init__(self, queue, no_wait):
        """
        Create frame queue.purge
        """
        self.queue = queue
        self.no_wait = no_wait

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(STRUCT_B.pack((self.no_wait << 0)))

    def get_size(self):  # type: () -> int
        return 4 + len(self.queue)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueuePurge
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        queue = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        no_wait = bool(_bit >> 0)
        offset += 1
        return cls(queue, no_wait)


class QueuePurgeOk(AMQPMethodPayload):
    """
    Confirms a queue purge
    
    This method confirms the purge of a queue.

    :param message_count: Reports the number of messages purged.
    :type message_count: int, 32 bit unsigned (message-count in AMQP)
    """
    __slots__ = (u'message_count',)

    NAME = u'queue.purge-ok'

    INDEX = (50, 31)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x1F'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'message-count', u'message-count', u'long', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueuePurgeOk(%s)' % (', '.join(map(repr,
                                                   [self.message_count])))

    def __init__(self, message_count):
        """
        Create frame queue.purge-ok
        """
        self.message_count = message_count

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_I.pack(self.message_count))

    def get_size(self):  # type: () -> int
        return 4

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueuePurgeOk
        offset = start_offset
        message_count, = STRUCT_I.unpack_from(buf, offset)
        offset += 4
        return cls(message_count)


class QueueUnbind(AMQPMethodPayload):
    """
    Unbind a queue from an exchange
    
    This method unbinds a queue from an exchange.

    :param queue: Specifies the name of the queue to unbind.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :param exchange: The name of the exchange to unbind from.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Routing key of binding
            Specifies the routing key of the binding to unbind.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    :param arguments: Arguments of binding
            Specifies the arguments of the binding to unbind.
    :type arguments: table. See coolamqp.uplink.framing.field_table (table in AMQP)
    """
    __slots__ = (
        u'queue',
        u'exchange',
        u'routing_key',
        u'arguments',
    )

    NAME = u'queue.unbind'

    INDEX = (50, 50)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x32'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
        Field(u'arguments', u'table', u'table', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueUnbind(%s)' % (', '.join(
            map(repr,
                [self.queue, self.exchange, self.routing_key, self.arguments
                 ])))

    def __init__(self, queue, exchange, routing_key, arguments):
        """
        Create frame queue.unbind
        """
        self.queue = queue
        self.exchange = exchange
        self.routing_key = routing_key
        self.arguments = arguments

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(STRUCT_B.pack(len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)
        enframe_table(buf, self.arguments)

    def get_size(self):  # type: () -> int
        return 5 + len(self.queue) + len(self.exchange) + len(
            self.routing_key) + frame_table_size(self.arguments)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueUnbind
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        queue = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        exchange = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        arguments, delta = deframe_table(buf, offset)
        offset += delta
        return cls(queue, exchange, routing_key, arguments)


class QueueUnbindOk(AMQPMethodPayload):
    """
    Confirm unbind successful
    
    This method confirms that the unbind was successful.

    """
    __slots__ = ()

    NAME = u'queue.unbind-ok'

    INDEX = (50, 51)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x32\x00\x33'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x32\x00\x33\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'QueueUnbindOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> QueueUnbindOk
        offset = start_offset
        return cls()


class Basic(AMQPClass):
    """
    The basic class provides methods that support an industry-standard
    
    messaging model.
    """
    NAME = u'basic'
    INDEX = 60


class BasicContentPropertyList(AMQPContentPropertyList):
    """
    The basic class provides methods that support an industry-standard
    
    messaging model.
    """
    FIELDS = [
        Field(u'content-type', u'shortstr', u'shortstr', False),
        Field(u'content-encoding', u'shortstr', u'shortstr', False),
        Field(u'headers', u'table', u'table', False),
        Field(u'delivery-mode', u'octet', u'octet', False),
        Field(u'priority', u'octet', u'octet', False),
        Field(u'correlation-id', u'shortstr', u'shortstr', False),
        Field(u'reply-to', u'shortstr', u'shortstr', False),
        Field(u'expiration', u'shortstr', u'shortstr', False),
        Field(u'message-id', u'shortstr', u'shortstr', False),
        Field(u'timestamp', u'timestamp', u'timestamp', False),
        Field(u'type', u'shortstr', u'shortstr', False),
        Field(u'user-id', u'shortstr', u'shortstr', False),
        Field(u'app-id', u'shortstr', u'shortstr', False),
        Field(u'reserved', u'shortstr', u'shortstr', False),
    ]
    # A dictionary from a zero property list to a class typized with
    # some fields
    PARTICULAR_CLASSES = {}

    def __new__(self, **kwargs):
        """
        Return a property list.
        :param content_type: MIME content type
        :type content_type: binary type (max length 255) (AMQP as shortstr)
        :param content_encoding: MIME content encoding
        :type content_encoding: binary type (max length 255) (AMQP as shortstr)
        :param headers: message header field table
        :type headers: table. See coolamqp.uplink.framing.field_table (AMQP as table)
        :param delivery_mode: non-persistent (1) or persistent (2)
        :type delivery_mode: int, 8 bit unsigned (AMQP as octet)
        :param priority: message priority, 0 to 9
        :type priority: int, 8 bit unsigned (AMQP as octet)
        :param correlation_id: application correlation identifier
        :type correlation_id: binary type (max length 255) (AMQP as shortstr)
        :param reply_to: address to reply to
        :type reply_to: binary type (max length 255) (AMQP as shortstr)
        :param expiration: message expiration specification
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
        zpf = bytearray([
            (('content_type' in kwargs) << 7) |
            (('content_encoding' in kwargs) << 6) |
            (('headers' in kwargs) << 5) | (('delivery_mode' in kwargs) << 4) |
            (('priority' in kwargs) << 3) | (('correlation_id' in kwargs) << 2)
            | (('reply_to' in kwargs) << 1) | int('expiration' in kwargs),
            (('message_id' in kwargs) << 7) | (('timestamp' in kwargs) << 6) |
            (('type_' in kwargs) << 5) | (('user_id' in kwargs) << 4) |
            (('app_id' in kwargs) << 3) | (('reserved' in kwargs) << 2)
        ])
        zpf = six.binary_type(zpf)

        #        If you know in advance what properties you will be using, use typized constructors like
        #
        #          runs once
        #            my_type = BasicContentPropertyList.typize('content_type', 'content_encoding')
        #
        #           runs many times
        #            props = my_type('text/plain', 'utf8')
        #
        #       instead of
        #
        #           # runs many times
        #           props = BasicContentPropertyList(content_type='text/plain', content_encoding='utf8')
        #
        #       This way you will be faster.
        #
        #       If you do not know in advance what properties you will be using, it is correct to use
        #       this constructor.
        if zpf in BasicContentPropertyList.PARTICULAR_CLASSES:
            return BasicContentPropertyList.PARTICULAR_CLASSES[zpf](**kwargs)
        else:
            logger.debug(
                'Property field (BasicContentPropertyList:%s) not seen yet, compiling',
                repr(zpf))
            c = compile_particular_content_property_list_class(
                zpf, BasicContentPropertyList.FIELDS)
            BasicContentPropertyList.PARTICULAR_CLASSES[zpf] = c
            return c(**kwargs)

    @staticmethod
    def typize(*fields):  # type: (*str) -> type
        zpf = bytearray([
            (('content_type' in fields) << 7) |
            (('content_encoding' in fields) << 6) |
            (('headers' in fields) << 5) | (('delivery_mode' in fields) << 4) |
            (('priority' in fields) << 3) | (('correlation_id' in fields) << 2)
            | (('reply_to' in fields) << 1) | int('expiration' in kwargs),
            (('message_id' in fields) << 7) | (('timestamp' in fields) << 6) |
            (('type_' in fields) << 5) | (('user_id' in fields) << 4) |
            (('app_id' in fields) << 3) | (('reserved' in fields) << 2)
        ])
        zpf = six.binary_type(zpf)
        if zpf in BasicContentPropertyList.PARTICULAR_CLASSES:
            return BasicContentPropertyList.PARTICULAR_CLASSES[zpf]
        else:
            logger.debug(
                'Property field (BasicContentPropertyList:%s) not seen yet, compiling',
                repr(zpf))
            c = compile_particular_content_property_list_class(
                zpf, BasicContentPropertyList.FIELDS)
            BasicContentPropertyList.PARTICULAR_CLASSES[zpf] = c
            return c

    @staticmethod
    def from_buffer(buf,
                    offset):  # type: (buffer, int) -> BasicContentPropertyList
        """
        Return a content property list instance unserialized from
        buffer, so that buf[offset] marks the start of property flags
        """
        # extract property flags
        pfl = 2
        if six.PY2:
            while ord(buf[offset + pfl - 1]) & 1:
                pfl += 2
        else:
            while buf[offset + pfl - 1] & 1:
                pfl += 2
        zpf = BasicContentPropertyList.zero_property_flags(buf[offset:offset +
                                                                      pfl]).tobytes()
        if zpf in BasicContentPropertyList.PARTICULAR_CLASSES:
            return BasicContentPropertyList.PARTICULAR_CLASSES[
                zpf].from_buffer(buf, offset)
        else:
            logger.debug(
                'Property field (BasicContentPropertyList:%s) not seen yet, compiling',
                repr(zpf))
            c = compile_particular_content_property_list_class(
                zpf, BasicContentPropertyList.FIELDS)
            BasicContentPropertyList.PARTICULAR_CLASSES[zpf] = c
            return c.from_buffer(buf, offset)


class BasicAck(AMQPMethodPayload):
    """
    Acknowledge one or more messages
    
    When sent by the client, this method acknowledges one or more
    messages delivered via the Deliver or Get-Ok methods.
    When sent by server, this method acknowledges one or more
    messages published with the Publish method on a channel in
    confirm mode.
    The acknowledgement can be for a single message or a set of
    messages up to and including a specific message.

    :type delivery_tag: int, 64 bit unsigned (delivery-tag in AMQP)
    :param multiple: Acknowledge multiple messages
            If set to 1, the delivery tag is treated as "up to and
            including", so that multiple messages can be acknowledged
            with a single method. If set to zero, the delivery tag
            refers to a single message. If the multiple field is 1, and
            the delivery tag is zero, this indicates acknowledgement of
            all outstanding messages.
    :type multiple: bool (bit in AMQP)
    """
    __slots__ = (
        u'delivery_tag',
        u'multiple',
    )

    NAME = u'basic.ack'

    INDEX = (60, 80)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x50'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'delivery-tag', u'delivery-tag', u'longlong', reserved=False),
        Field(u'multiple', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicAck(%s)' % (', '.join(
            map(repr, [self.delivery_tag, self.multiple])))

    def __init__(self, delivery_tag, multiple):
        """
        Create frame basic.ack
        """
        self.delivery_tag = delivery_tag
        self.multiple = multiple

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_QB.pack(self.delivery_tag, (self.multiple << 0)))

    def get_size(self):  # type: () -> int
        return 9

    @classmethod
    def from_buffer(cls, buf, start_offset):  # type: (buffer, int) -> BasicAck
        offset = start_offset
        delivery_tag, _bit, = STRUCT_QB.unpack_from(buf, offset)
        offset += 8
        multiple = bool(_bit >> 0)
        offset += 1
        return cls(delivery_tag, multiple)


class BasicConsume(AMQPMethodPayload):
    """
    Start a queue consumer
    
    This method asks the server to start a "consumer", which is a
    transient request for
    messages from a specific queue. Consumers last as long as the
    channel they were
    declared on, or until the client cancels them.

    :param queue: Specifies the name of the queue to consume from.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :param consumer_tag: Specifies the identifier for the consumer. the consumer tag
            is local to a
            channel, so two clients can use the same consumer tags. If
            this field is
            empty the server will generate a unique tag.
    :type consumer_tag: binary type (max length 255) (consumer-tag in AMQP)
    :type no_local: bool (no-local in AMQP)
    :type no_ack: bool (no-ack in AMQP)
    :param exclusive: Request exclusive access
            Request exclusive consumer access, meaning only this
            consumer can access the
            queue.
    :type exclusive: bool (bit in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    :param arguments: Arguments for declaration
            A set of arguments for the consume. The syntax and semantics
            of these
            arguments depends on the server implementation.
    :type arguments: table. See coolamqp.uplink.framing.field_table (table in AMQP)
    """
    __slots__ = (
        u'queue',
        u'consumer_tag',
        u'no_local',
        u'no_ack',
        u'exclusive',
        u'no_wait',
        u'arguments',
    )

    NAME = u'basic.consume'

    INDEX = (60, 20)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x14'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'consumer-tag', u'consumer-tag', u'shortstr', reserved=False),
        Field(u'no-local', u'no-local', u'bit', reserved=False),
        Field(u'no-ack', u'no-ack', u'bit', reserved=False),
        Field(u'exclusive', u'bit', u'bit', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
        Field(u'arguments', u'table', u'table', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicConsume(%s)' % (', '.join(
            map(repr, [
                self.queue, self.consumer_tag, self.no_local, self.no_ack,
                self.exclusive, self.no_wait, self.arguments
            ])))

    def __init__(self, queue, consumer_tag, no_local, no_ack, exclusive,
                 no_wait, arguments):
        """
        Create frame basic.consume
        """
        self.queue = queue
        self.consumer_tag = consumer_tag
        self.no_local = no_local
        self.no_ack = no_ack
        self.exclusive = exclusive
        self.no_wait = no_wait
        self.arguments = arguments

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(STRUCT_B.pack(len(self.consumer_tag)))
        buf.write(self.consumer_tag)
        buf.write(
            STRUCT_B.pack((self.no_local << 0) | (self.no_ack << 1)
                          | (self.exclusive << 2) | (self.no_wait << 3)))
        enframe_table(buf, self.arguments)

    def get_size(self):  # type: () -> int
        return 5 + len(self.queue) + len(self.consumer_tag) + frame_table_size(
            self.arguments)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicConsume
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        queue = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        consumer_tag = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        no_local = bool(_bit >> 0)
        no_ack = bool(_bit >> 1)
        exclusive = bool(_bit >> 2)
        no_wait = bool(_bit >> 3)
        offset += 1
        arguments, delta = deframe_table(buf, offset)
        offset += delta
        return cls(queue, consumer_tag, no_local, no_ack, exclusive, no_wait,
                   arguments)


class BasicCancel(AMQPMethodPayload):
    """
    End a queue consumer
    
    This method cancels a consumer. This does not affect already
    delivered
    messages, but it does mean the server will not send any more
    messages for
    that consumer. The client may receive an arbitrary number of
    messages in
    between sending the cancel method and receiving the cancel-ok
    reply.
    It may also be sent from the server to the client in the event
    of the consumer being unexpectedly cancelled (i.e. cancelled
    for any reason other than the server receiving the
    corresponding basic.cancel from the client). This allows
    clients to be notified of the loss of consumers due to events
    such as queue deletion. Note that as it is not a MUST for
    clients to accept this method from the server, it is advisable
    for the broker to be able to identify those clients that are
    capable of accepting the method, through some means of
    capability negotiation.

    :type consumer_tag: binary type (max length 255) (consumer-tag in AMQP)
    :type no_wait: bool (no-wait in AMQP)
    """
    __slots__ = (
        u'consumer_tag',
        u'no_wait',
    )

    NAME = u'basic.cancel'

    INDEX = (60, 30)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x1E'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'consumer-tag', u'consumer-tag', u'shortstr', reserved=False),
        Field(u'no-wait', u'no-wait', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicCancel(%s)' % (', '.join(
            map(repr, [self.consumer_tag, self.no_wait])))

    def __init__(self, consumer_tag, no_wait):
        """
        Create frame basic.cancel
        """
        self.consumer_tag = consumer_tag
        self.no_wait = no_wait

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack(len(self.consumer_tag)))
        buf.write(self.consumer_tag)
        buf.write(STRUCT_B.pack((self.no_wait << 0)))

    def get_size(self):  # type: () -> int
        return 2 + len(self.consumer_tag)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicCancel
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        consumer_tag = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        no_wait = bool(_bit >> 0)
        offset += 1
        return cls(consumer_tag, no_wait)


class BasicConsumeOk(AMQPMethodPayload):
    """
    Confirm a new consumer
    
    The server provides the client with a consumer tag, which is
    used by the client
    for methods called on the consumer at a later stage.

    :param consumer_tag: Holds the consumer tag specified by the client or provided
            by the server.
    :type consumer_tag: binary type (max length 255) (consumer-tag in AMQP)
    """
    __slots__ = (u'consumer_tag',)

    NAME = u'basic.consume-ok'

    INDEX = (60, 21)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x15'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'consumer-tag', u'consumer-tag', u'shortstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicConsumeOk(%s)' % (', '.join(map(repr,
                                                     [self.consumer_tag])))

    def __init__(self, consumer_tag):
        """
        Create frame basic.consume-ok
        """
        self.consumer_tag = consumer_tag

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack(len(self.consumer_tag)))
        buf.write(self.consumer_tag)

    def get_size(self):  # type: () -> int
        return 1 + len(self.consumer_tag)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicConsumeOk
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        consumer_tag = buf[offset:offset + s_len]
        offset += s_len
        return cls(consumer_tag)


class BasicCancelOk(AMQPMethodPayload):
    """
    Confirm a cancelled consumer
    
    This method confirms that the cancellation was completed.

    :type consumer_tag: binary type (max length 255) (consumer-tag in AMQP)
    """
    __slots__ = (u'consumer_tag',)

    NAME = u'basic.cancel-ok'

    INDEX = (60, 31)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x1F'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'consumer-tag', u'consumer-tag', u'shortstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicCancelOk(%s)' % (', '.join(map(repr,
                                                    [self.consumer_tag])))

    def __init__(self, consumer_tag):
        """
        Create frame basic.cancel-ok
        """
        self.consumer_tag = consumer_tag

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack(len(self.consumer_tag)))
        buf.write(self.consumer_tag)

    def get_size(self):  # type: () -> int
        return 1 + len(self.consumer_tag)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicCancelOk
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        consumer_tag = buf[offset:offset + s_len]
        offset += s_len
        return cls(consumer_tag)


class BasicDeliver(AMQPMethodPayload):
    """
    Notify the client of a consumer message
    
    This method delivers a message to the client, via a consumer. In
    the asynchronous
    message delivery model, the client starts a consumer using the
    Consume method, then
    the server responds with Deliver methods as and when messages
    arrive for that
    consumer.

    :type consumer_tag: binary type (max length 255) (consumer-tag in AMQP)
    :type delivery_tag: int, 64 bit unsigned (delivery-tag in AMQP)
    :type redelivered: bool (redelivered in AMQP)
    :param exchange: Specifies the name of the exchange that the message was
            originally published to.
            May be empty, indicating the default exchange.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Message routing key
            Specifies the routing key name specified when the message
            was published.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    """
    __slots__ = (
        u'consumer_tag',
        u'delivery_tag',
        u'redelivered',
        u'exchange',
        u'routing_key',
    )

    NAME = u'basic.deliver'

    INDEX = (60, 60)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x3C'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'consumer-tag', u'consumer-tag', u'shortstr', reserved=False),
        Field(u'delivery-tag', u'delivery-tag', u'longlong', reserved=False),
        Field(u'redelivered', u'redelivered', u'bit', reserved=False),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicDeliver(%s)' % (', '.join(
            map(repr, [
                self.consumer_tag, self.delivery_tag, self.redelivered,
                self.exchange, self.routing_key
            ])))

    def __init__(self, consumer_tag, delivery_tag, redelivered, exchange,
                 routing_key):
        """
        Create frame basic.deliver
        """
        self.consumer_tag = consumer_tag
        self.delivery_tag = delivery_tag
        self.redelivered = redelivered
        self.exchange = exchange
        self.routing_key = routing_key

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack(len(self.consumer_tag)))
        buf.write(self.consumer_tag)
        buf.write(
            STRUCT_QBB.pack(self.delivery_tag, (self.redelivered << 0),
                            len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)

    def get_size(self):  # type: () -> int
        return 12 + len(self.consumer_tag) + len(self.exchange) + len(
            self.routing_key)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicDeliver
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        consumer_tag = buf[offset:offset + s_len]
        offset += s_len
        delivery_tag, _bit, = STRUCT_QB.unpack_from(buf, offset)
        offset += 8
        redelivered = bool(_bit >> 0)
        offset += 1
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        exchange = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        return cls(consumer_tag, delivery_tag, redelivered, exchange,
                   routing_key)


class BasicGet(AMQPMethodPayload):
    """
    Direct access to a queue
    
    This method provides a direct access to the messages in a queue
    using a synchronous
    dialogue that is designed for specific types of application
    where synchronous
    functionality is more important than performance.

    :param queue: Specifies the name of the queue to get a message from.
    :type queue: binary type (max length 255) (queue-name in AMQP)
    :type no_ack: bool (no-ack in AMQP)
    """
    __slots__ = (
        u'queue',
        u'no_ack',
    )

    NAME = u'basic.get'

    INDEX = (60, 70)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x46'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'queue', u'queue-name', u'shortstr', reserved=False),
        Field(u'no-ack', u'no-ack', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicGet(%s)' % (', '.join(map(repr,
                                               [self.queue, self.no_ack])))

    def __init__(self, queue, no_ack):
        """
        Create frame basic.get
        """
        self.queue = queue
        self.no_ack = no_ack

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.queue)))
        buf.write(self.queue)
        buf.write(STRUCT_B.pack((self.no_ack << 0)))

    def get_size(self):  # type: () -> int
        return 4 + len(self.queue)

    @classmethod
    def from_buffer(cls, buf, start_offset):  # type: (buffer, int) -> BasicGet
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        queue = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        no_ack = bool(_bit >> 0)
        offset += 1
        return cls(queue, no_ack)


class BasicGetOk(AMQPMethodPayload):
    """
    Provide client with a message
    
    This method delivers a message to the client following a get
    method. A message
    delivered by 'get-ok' must be acknowledged unless the no-ack
    option was set in the
    get method.

    :type delivery_tag: int, 64 bit unsigned (delivery-tag in AMQP)
    :type redelivered: bool (redelivered in AMQP)
    :param exchange: Specifies the name of the exchange that the message was
            originally published to.
            If empty, the message was published to the default exchange.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Message routing key
            Specifies the routing key name specified when the message
            was published.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    :type message_count: int, 32 bit unsigned (message-count in AMQP)
    """
    __slots__ = (
        u'delivery_tag',
        u'redelivered',
        u'exchange',
        u'routing_key',
        u'message_count',
    )

    NAME = u'basic.get-ok'

    INDEX = (60, 71)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x47'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'delivery-tag', u'delivery-tag', u'longlong', reserved=False),
        Field(u'redelivered', u'redelivered', u'bit', reserved=False),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
        Field(u'message-count', u'message-count', u'long', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicGetOk(%s)' % (', '.join(
            map(repr, [
                self.delivery_tag, self.redelivered, self.exchange,
                self.routing_key, self.message_count
            ])))

    def __init__(self, delivery_tag, redelivered, exchange, routing_key,
                 message_count):
        """
        Create frame basic.get-ok
        """
        self.delivery_tag = delivery_tag
        self.redelivered = redelivered
        self.exchange = exchange
        self.routing_key = routing_key
        self.message_count = message_count

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(
            STRUCT_QBB.pack(self.delivery_tag, (self.redelivered << 0),
                            len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)
        buf.write(STRUCT_I.pack(self.message_count))

    def get_size(self):  # type: () -> int
        return 15 + len(self.exchange) + len(self.routing_key)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicGetOk
        offset = start_offset
        delivery_tag, _bit, = STRUCT_QB.unpack_from(buf, offset)
        offset += 8
        redelivered = bool(_bit >> 0)
        offset += 1
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        exchange = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        message_count, = STRUCT_I.unpack_from(buf, offset)
        offset += 4
        return cls(delivery_tag, redelivered, exchange, routing_key,
                   message_count)


class BasicGetEmpty(AMQPMethodPayload):
    """
    Indicate no messages available
    
    This method tells the client that the queue has no messages
    available for the
    client.

    """
    __slots__ = ()

    NAME = u'basic.get-empty'

    INDEX = (60, 72)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x48'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x0D\x00\x3C\x00\x48\x00\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'shortstr', u'shortstr', reserved=True),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicGetEmpty(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicGetEmpty
        offset = start_offset
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        offset += s_len  # reserved field!
        return cls()


class BasicNack(AMQPMethodPayload):
    """
    Reject one or more incoming messages
    
    This method allows a client to reject one or more incoming
    messages. It can be
    used to interrupt and cancel large incoming messages, or return
    untreatable
    messages to their original queue.
    This method is also used by the server to inform publishers on
    channels in
    confirm mode of unhandled messages. If a publisher receives this
    method, it
    probably needs to republish the offending messages.

    :type delivery_tag: int, 64 bit unsigned (delivery-tag in AMQP)
    :param multiple: Reject multiple messages
            If set to 1, the delivery tag is treated as "up to and
            including", so that multiple messages can be rejected
            with a single method. If set to zero, the delivery tag
            refers to a single message. If the multiple field is 1, and
            the delivery tag is zero, this indicates rejection of
            all outstanding messages.
    :type multiple: bool (bit in AMQP)
    :param requeue: Requeue the message
            If requeue is true, the server will attempt to requeue the
            message. If requeue
            is false or the requeue attempt fails the messages are
            discarded or dead-lettered.
            Clients receiving the Nack methods should ignore this flag.
    :type requeue: bool (bit in AMQP)
    """
    __slots__ = (
        u'delivery_tag',
        u'multiple',
        u'requeue',
    )

    NAME = u'basic.nack'

    INDEX = (60, 120)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x78'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'delivery-tag', u'delivery-tag', u'longlong', reserved=False),
        Field(u'multiple', u'bit', u'bit', reserved=False),
        Field(u'requeue', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicNack(%s)' % (', '.join(
            map(repr, [self.delivery_tag, self.multiple, self.requeue])))

    def __init__(self, delivery_tag, multiple, requeue):
        """
        Create frame basic.nack
        """
        self.delivery_tag = delivery_tag
        self.multiple = multiple
        self.requeue = requeue

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(
            STRUCT_QB.pack(self.delivery_tag,
                           (self.multiple << 0) | (self.requeue << 1)))

    def get_size(self):  # type: () -> int
        return 9

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicNack
        offset = start_offset
        delivery_tag, _bit, = STRUCT_QB.unpack_from(buf, offset)
        offset += 8
        multiple = bool(_bit >> 0)
        requeue = bool(_bit >> 1)
        offset += 1
        return cls(delivery_tag, multiple, requeue)


class BasicPublish(AMQPMethodPayload):
    """
    Publish a message
    
    This method publishes a message to a specific exchange. The
    message will be routed
    to queues as defined by the exchange configuration and
    distributed to any active
    consumers when the transaction, if any, is committed.

    :param exchange: Specifies the name of the exchange to publish to. the
            exchange name can be
            empty, meaning the default exchange. If the exchange name is
            specified, and that
            exchange does not exist, the server will raise a channel
            exception.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Message routing key
            Specifies the routing key for the message. The routing key
            is used for routing
            messages depending on the exchange configuration.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    :param mandatory: Indicate mandatory routing
            This flag tells the server how to react if the message
            cannot be routed to a
            queue. If this flag is set, the server will return an
            unroutable message with a
            Return method. If this flag is zero, the server silently
            drops the message.
    :type mandatory: bool (bit in AMQP)
    :param immediate: Request immediate delivery
            This flag tells the server how to react if the message
            cannot be routed to a
            queue consumer immediately. If this flag is set, the server
            will return an
            undeliverable message with a Return method. If this flag is
            zero, the server
            will queue the message, but with no guarantee that it will
            ever be consumed.
    :type immediate: bool (bit in AMQP)
    """
    __slots__ = (
        u'exchange',
        u'routing_key',
        u'mandatory',
        u'immediate',
    )

    NAME = u'basic.publish'

    INDEX = (60, 40)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x28'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reserved-1', u'short', u'short', reserved=True),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
        Field(u'mandatory', u'bit', u'bit', reserved=False),
        Field(u'immediate', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicPublish(%s)' % (', '.join(
            map(repr, [
                self.exchange, self.routing_key, self.mandatory, self.immediate
            ])))

    def __init__(self, exchange, routing_key, mandatory, immediate):
        """
        Create frame basic.publish
        """
        self.exchange = exchange
        self.routing_key = routing_key
        self.mandatory = mandatory
        self.immediate = immediate

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(b'\x00\x00')
        buf.write(STRUCT_B.pack(len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)
        buf.write(STRUCT_B.pack((self.mandatory << 0) | (self.immediate << 1)))

    def get_size(self):  # type: () -> int
        return 5 + len(self.exchange) + len(self.routing_key)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicPublish
        offset = start_offset
        s_len, = STRUCT_2xB.unpack_from(buf, offset)
        offset += 3
        exchange = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        mandatory = bool(_bit >> 0)
        immediate = bool(_bit >> 1)
        offset += 1
        return cls(exchange, routing_key, mandatory, immediate)


class BasicQos(AMQPMethodPayload):
    """
    Specify quality of service
    
    This method requests a specific quality of service. The QoS can
    be specified for the
    current channel or for all channels on the connection. The
    particular properties and
    semantics of a qos method always depend on the content class
    semantics. Though the
    qos method could in principle apply to both peers, it is
    currently meaningful only
    for the server.

    :param prefetch_size: Prefetch window in octets
            The client can request that messages be sent in advance so
            that when the client
            finishes processing a message, the following message is
            already held locally,
            rather than needing to be sent down the channel. Prefetching
            gives a performance
            improvement. This field specifies the prefetch window size
            in octets. The server
            will send a message in advance if it is equal to or smaller
            in size than the
            available prefetch size (and also falls into other prefetch
            limits). May be set
            to zero, meaning "no specific limit", although other
            prefetch limits may still
            apply. The prefetch-size is ignored if the no-ack option is
            set.
    :type prefetch_size: int, 32 bit unsigned (long in AMQP)
    :param prefetch_count: Prefetch window in messages
            Specifies a prefetch window in terms of whole messages. This
            field may be used
            in combination with the prefetch-size field; a message will
            only be sent in
            advance if both prefetch windows (and those at the channel
            and connection level)
            allow it. The prefetch-count is ignored if the no-ack option
            is set.
    :type prefetch_count: int, 16 bit unsigned (short in AMQP)
    :param global_: Apply to entire connection
            RabbitMQ has reinterpreted this field. The original
            specification said: "By default the QoS settings apply to
            the current channel only. If this field is set, they are
            applied to the entire connection." Instead, RabbitMQ takes
            global=false to mean that the QoS settings should apply
            per-consumer (for new consumers on the channel; existing
            ones being unaffected) and global=true to mean that the QoS
            settings should apply per-channel.
    :type global_: bool (bit in AMQP)
    """
    __slots__ = (
        u'prefetch_size',
        u'prefetch_count',
        u'global_',
    )

    NAME = u'basic.qos'

    INDEX = (60, 10)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x0A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'prefetch-size', u'long', u'long', reserved=False),
        Field(u'prefetch-count', u'short', u'short', reserved=False),
        Field(u'global', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicQos(%s)' % (', '.join(
            map(repr,
                [self.prefetch_size, self.prefetch_count, self.global_])))

    def __init__(self, prefetch_size, prefetch_count, global_):
        """
        Create frame basic.qos
        """
        self.prefetch_size = prefetch_size
        self.prefetch_count = prefetch_count
        self.global_ = global_

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(
            STRUCT_IHB.pack(self.prefetch_size, self.prefetch_count,
                            (self.global_ << 0)))

    def get_size(self):  # type: () -> int
        return 7

    @classmethod
    def from_buffer(cls, buf, start_offset):  # type: (buffer, int) -> BasicQos
        offset = start_offset
        prefetch_size, prefetch_count, _bit, = STRUCT_IHB.unpack_from(
            buf, offset)
        offset += 6
        global_ = bool(_bit >> 0)
        offset += 1
        return cls(prefetch_size, prefetch_count, global_)


class BasicQosOk(AMQPMethodPayload):
    """
    Confirm the requested qos
    
    This method tells the client that the requested QoS levels could
    be handled by the
    server. The requested QoS applies to all active consumers until
    a new QoS is
    defined.

    """
    __slots__ = ()

    NAME = u'basic.qos-ok'

    INDEX = (60, 11)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x0B'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x3C\x00\x0B\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicQosOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicQosOk
        offset = start_offset
        return cls()


class BasicReturn(AMQPMethodPayload):
    """
    Return a failed message
    
    This method returns an undeliverable message that was published
    with the "immediate"
    flag set, or an unroutable message published with the
    "mandatory" flag set. The
    reply code and text provide information about the reason that
    the message was
    undeliverable.

    :type reply_code: int, 16 bit unsigned (reply-code in AMQP)
    :type reply_text: binary type (max length 255) (reply-text in AMQP)
    :param exchange: Specifies the name of the exchange that the message was
            originally published
            to. May be empty, meaning the default exchange.
    :type exchange: binary type (max length 255) (exchange-name in AMQP)
    :param routing_key: Message routing key
            Specifies the routing key name specified when the message
            was published.
    :type routing_key: binary type (max length 255) (shortstr in AMQP)
    """
    __slots__ = (
        u'reply_code',
        u'reply_text',
        u'exchange',
        u'routing_key',
    )

    NAME = u'basic.return'

    INDEX = (60, 50)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x32'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = False  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'reply-code', u'reply-code', u'short', reserved=False),
        Field(u'reply-text', u'reply-text', u'shortstr', reserved=False),
        Field(u'exchange', u'exchange-name', u'shortstr', reserved=False),
        Field(u'routing-key', u'shortstr', u'shortstr', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicReturn(%s)' % (', '.join(
            map(repr, [
                self.reply_code, self.reply_text, self.exchange,
                self.routing_key
            ])))

    def __init__(self, reply_code, reply_text, exchange, routing_key):
        """
        Create frame basic.return
        """
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.exchange = exchange
        self.routing_key = routing_key

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_HB.pack(self.reply_code, len(self.reply_text)))
        buf.write(self.reply_text)
        buf.write(STRUCT_B.pack(len(self.exchange)))
        buf.write(self.exchange)
        buf.write(STRUCT_B.pack(len(self.routing_key)))
        buf.write(self.routing_key)

    def get_size(self):  # type: () -> int
        return 5 + len(self.reply_text) + len(self.exchange) + len(
            self.routing_key)

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicReturn
        offset = start_offset
        reply_code, s_len, = STRUCT_HB.unpack_from(buf, offset)
        offset += 3
        reply_text = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        exchange = buf[offset:offset + s_len]
        offset += s_len
        s_len, = STRUCT_B.unpack_from(buf, offset)
        offset += 1
        routing_key = buf[offset:offset + s_len]
        offset += s_len
        return cls(reply_code, reply_text, exchange, routing_key)


class BasicReject(AMQPMethodPayload):
    """
    Reject an incoming message
    
    This method allows a client to reject a message. It can be used
    to interrupt and
    cancel large incoming messages, or return untreatable messages
    to their original
    queue.

    :type delivery_tag: int, 64 bit unsigned (delivery-tag in AMQP)
    :param requeue: Requeue the message
            If requeue is true, the server will attempt to requeue the
            message. If requeue
            is false or the requeue attempt fails the messages are
            discarded or dead-lettered.
    :type requeue: bool (bit in AMQP)
    """
    __slots__ = (
        u'delivery_tag',
        u'requeue',
    )

    NAME = u'basic.reject'

    INDEX = (60, 90)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x5A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'delivery-tag', u'delivery-tag', u'longlong', reserved=False),
        Field(u'requeue', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicReject(%s)' % (', '.join(
            map(repr, [self.delivery_tag, self.requeue])))

    def __init__(self, delivery_tag, requeue):
        """
        Create frame basic.reject
        """
        self.delivery_tag = delivery_tag
        self.requeue = requeue

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_QB.pack(self.delivery_tag, (self.requeue << 0)))

    def get_size(self):  # type: () -> int
        return 9

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicReject
        offset = start_offset
        delivery_tag, _bit, = STRUCT_QB.unpack_from(buf, offset)
        offset += 8
        requeue = bool(_bit >> 0)
        offset += 1
        return cls(delivery_tag, requeue)


class BasicRecoverAsync(AMQPMethodPayload):
    """
    Redeliver unacknowledged messages
    
    This method asks the server to redeliver all unacknowledged
    messages on a
    specified channel. Zero or more messages may be redelivered.
    This method
    is deprecated in favour of the synchronous Recover/Recover-Ok.

    :param requeue: Requeue the message
            If this field is zero, the message will be redelivered to
            the original
            recipient. If this bit is 1, the server will attempt to
            requeue the message,
            potentially then delivering it to an alternative subscriber.
    :type requeue: bool (bit in AMQP)
    """
    __slots__ = (u'requeue',)

    NAME = u'basic.recover-async'

    INDEX = (60, 100)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x64'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'requeue', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicRecoverAsync(%s)' % (', '.join(map(repr, [self.requeue])))

    def __init__(self, requeue):
        """
        Create frame basic.recover-async
        """
        self.requeue = requeue

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack((self.requeue << 0)))

    def get_size(self):  # type: () -> int
        return 1

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicRecoverAsync
        offset = start_offset
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        requeue = bool(_bit >> 0)
        offset += 1
        return cls(requeue)


class BasicRecover(AMQPMethodPayload):
    """
    Redeliver unacknowledged messages
    
    This method asks the server to redeliver all unacknowledged
    messages on a
    specified channel. Zero or more messages may be redelivered.
    This method
    replaces the asynchronous Recover.

    :param requeue: Requeue the message
            If this field is zero, the message will be redelivered to
            the original
            recipient. If this bit is 1, the server will attempt to
            requeue the message,
            potentially then delivering it to an alternative subscriber.
    :type requeue: bool (bit in AMQP)
    """
    __slots__ = (u'requeue',)

    NAME = u'basic.recover'

    INDEX = (60, 110)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x6E'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'requeue', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicRecover(%s)' % (', '.join(map(repr, [self.requeue])))

    def __init__(self, requeue):
        """
        Create frame basic.recover
        """
        self.requeue = requeue

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack((self.requeue << 0)))

    def get_size(self):  # type: () -> int
        return 1

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicRecover
        offset = start_offset
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        requeue = bool(_bit >> 0)
        offset += 1
        return cls(requeue)


class BasicRecoverOk(AMQPMethodPayload):
    """
    Confirm recovery
    
    This method acknowledges a Basic.Recover method.

    """
    __slots__ = ()

    NAME = u'basic.recover-ok'

    INDEX = (60, 111)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x3C\x00\x6F'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x3C\x00\x6F\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'BasicRecoverOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> BasicRecoverOk
        offset = start_offset
        return cls()


class Tx(AMQPClass):
    """
    The tx class allows publish and ack operations to be batched into
    
    atomic
    units of work. The intention is that all publish and ack requests
    issued
    within a transaction will complete successfully or none of them
    will.
    Servers SHOULD implement atomic transactions at least where all
    publish
    or ack requests affect a single queue. Transactions that cover
    multiple
    queues may be non-atomic, given that queues can be created and
    destroyed
    asynchronously, and such events do not form part of any transaction.
    Further, the behaviour of transactions with respect to the immediate
    and
    mandatory flags on Basic.Publish methods is not defined.
    """
    NAME = u'tx'
    INDEX = 90


class TxCommit(AMQPMethodPayload):
    """
    Commit the current transaction
    
    This method commits all message publications and acknowledgments
    performed in
    the current transaction. A new transaction starts immediately
    after a commit.

    """
    __slots__ = ()

    NAME = u'tx.commit'

    INDEX = (90, 20)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x5A\x00\x14'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x5A\x00\x14\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'TxCommit(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf, start_offset):  # type: (buffer, int) -> TxCommit
        offset = start_offset
        return cls()


class TxCommitOk(AMQPMethodPayload):
    """
    Confirm a successful commit
    
    This method confirms to the client that the commit succeeded.
    Note that if a commit
    fails, the server raises a channel exception.

    """
    __slots__ = ()

    NAME = u'tx.commit-ok'

    INDEX = (90, 21)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x5A\x00\x15'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x5A\x00\x15\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'TxCommitOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> TxCommitOk
        offset = start_offset
        return cls()


class TxRollback(AMQPMethodPayload):
    """
    Abandon the current transaction
    
    This method abandons all message publications and
    acknowledgments performed in
    the current transaction. A new transaction starts immediately
    after a rollback.
    Note that unacked messages will not be automatically redelivered
    by rollback;
    if that is required an explicit recover call should be issued.

    """
    __slots__ = ()

    NAME = u'tx.rollback'

    INDEX = (90, 30)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x5A\x00\x1E'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x5A\x00\x1E\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'TxRollback(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> TxRollback
        offset = start_offset
        return cls()


class TxRollbackOk(AMQPMethodPayload):
    """
    Confirm successful rollback
    
    This method confirms to the client that the rollback succeeded.
    Note that if an
    rollback fails, the server raises a channel exception.

    """
    __slots__ = ()

    NAME = u'tx.rollback-ok'

    INDEX = (90, 31)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x5A\x00\x1F'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x5A\x00\x1F\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'TxRollbackOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> TxRollbackOk
        offset = start_offset
        return cls()


class TxSelect(AMQPMethodPayload):
    """
    Select standard transaction mode
    
    This method sets the channel to use standard transactions. The
    client must use this
    method at least once on a channel before using the Commit or
    Rollback methods.

    """
    __slots__ = ()

    NAME = u'tx.select'

    INDEX = (90, 10)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x5A\x00\x0A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x5A\x00\x0A\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'TxSelect(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf, start_offset):  # type: (buffer, int) -> TxSelect
        offset = start_offset
        return cls()


class TxSelectOk(AMQPMethodPayload):
    """
    Confirm transaction mode
    
    This method confirms to the client that the channel was
    successfully set to use
    standard transactions.

    """
    __slots__ = ()

    NAME = u'tx.select-ok'

    INDEX = (90, 11)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x5A\x00\x0B'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x5A\x00\x0B\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'TxSelectOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> TxSelectOk
        offset = start_offset
        return cls()


class Confirm(AMQPClass):
    """
    The confirm class allows publishers to put the channel in
    
    confirm mode and subsequently be notified when messages have been
    handled by the broker. The intention is that all messages
    published on a channel in confirm mode will be acknowledged at
    some point. By acknowledging a message the broker assumes
    responsibility for it and indicates that it has done something
    it deems reasonable with it.
    Unroutable mandatory or immediate messages are acknowledged
    right after the Basic.Return method. Messages are acknowledged
    when all queues to which the message has been routed
    have either delivered the message and received an
    acknowledgement (if required), or enqueued the message (and
    persisted it if required).
    Published messages are assigned ascending sequence numbers,
    starting at 1 with the first Confirm.Select method. The server
    confirms messages by sending Basic.Ack methods referring to these
    sequence numbers.
    """
    NAME = u'confirm'
    INDEX = 85


class ConfirmSelect(AMQPMethodPayload):
    """
    This method sets the channel to use publisher acknowledgements.
    
    The client can only use this method on a non-transactional
    channel.

    :param nowait: If set, the server will not respond to the method. the
            client should
            not wait for a reply method. If the server could not
            complete the
            method it will raise a channel or connection exception.
    :type nowait: bool (bit in AMQP)
    """
    __slots__ = (u'nowait',)

    NAME = u'confirm.select'

    INDEX = (85, 10)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x55\x00\x0A'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = False, True

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = False  # this means that argument part has always the same content

    # See constructor pydoc for details
    FIELDS = [
        Field(u'nowait', u'bit', u'bit', reserved=False),
    ]

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConfirmSelect(%s)' % (', '.join(map(repr, [self.nowait])))

    def __init__(self, nowait):
        """
        Create frame confirm.select
        """
        self.nowait = nowait

    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None
        buf.write(STRUCT_B.pack((self.nowait << 0)))

    def get_size(self):  # type: () -> int
        return 1

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConfirmSelect
        offset = start_offset
        _bit, = STRUCT_B.unpack_from(buf, offset)
        offset += 0
        nowait = bool(_bit >> 0)
        offset += 1
        return cls(nowait)


class ConfirmSelectOk(AMQPMethodPayload):
    """
    This method confirms to the client that the channel was
    
    successfully
    set to use publisher acknowledgements.

    """
    __slots__ = ()

    NAME = u'confirm.select-ok'

    INDEX = (85, 11)  # (Class ID, Method ID)
    BINARY_HEADER = b'\x00\x55\x00\x0B'  # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = True, False

    IS_SIZE_STATIC = True  # this means that argument part has always the same length
    IS_CONTENT_STATIC = True  # this means that argument part has always the same content
    STATIC_CONTENT = b'\x00\x00\x00\x04\x00\x55\x00\x0B\xCE'  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END

    def __repr__(self):  # type: () -> str
        """
        Convert the frame to a Python-representable string

        :return: Python string representation
        """
        return 'ConfirmSelectOk(%s)' % (', '.join(map(repr, [])))

    @classmethod
    def from_buffer(cls, buf,
                    start_offset):  # type: (buffer, int) -> ConfirmSelectOk
        offset = start_offset
        return cls()


IDENT_TO_METHOD = {
    (10, 60): ConnectionBlocked,
    (10, 50): ConnectionClose,
    (10, 51): ConnectionCloseOk,
    (10, 40): ConnectionOpen,
    (10, 41): ConnectionOpenOk,
    (10, 10): ConnectionStart,
    (10, 20): ConnectionSecure,
    (10, 11): ConnectionStartOk,
    (10, 21): ConnectionSecureOk,
    (10, 30): ConnectionTune,
    (10, 31): ConnectionTuneOk,
    (10, 61): ConnectionUnblocked,
    (20, 40): ChannelClose,
    (20, 41): ChannelCloseOk,
    (20, 20): ChannelFlow,
    (20, 21): ChannelFlowOk,
    (20, 10): ChannelOpen,
    (20, 11): ChannelOpenOk,
    (40, 30): ExchangeBind,
    (40, 31): ExchangeBindOk,
    (40, 10): ExchangeDeclare,
    (40, 20): ExchangeDelete,
    (40, 11): ExchangeDeclareOk,
    (40, 21): ExchangeDeleteOk,
    (40, 40): ExchangeUnbind,
    (40, 51): ExchangeUnbindOk,
    (50, 20): QueueBind,
    (50, 21): QueueBindOk,
    (50, 10): QueueDeclare,
    (50, 40): QueueDelete,
    (50, 11): QueueDeclareOk,
    (50, 41): QueueDeleteOk,
    (50, 30): QueuePurge,
    (50, 31): QueuePurgeOk,
    (50, 50): QueueUnbind,
    (50, 51): QueueUnbindOk,
    (60, 80): BasicAck,
    (60, 20): BasicConsume,
    (60, 30): BasicCancel,
    (60, 21): BasicConsumeOk,
    (60, 31): BasicCancelOk,
    (60, 60): BasicDeliver,
    (60, 70): BasicGet,
    (60, 71): BasicGetOk,
    (60, 72): BasicGetEmpty,
    (60, 120): BasicNack,
    (60, 40): BasicPublish,
    (60, 10): BasicQos,
    (60, 11): BasicQosOk,
    (60, 50): BasicReturn,
    (60, 90): BasicReject,
    (60, 100): BasicRecoverAsync,
    (60, 110): BasicRecover,
    (60, 111): BasicRecoverOk,
    (90, 20): TxCommit,
    (90, 21): TxCommitOk,
    (90, 30): TxRollback,
    (90, 31): TxRollbackOk,
    (90, 10): TxSelect,
    (90, 11): TxSelectOk,
    (85, 10): ConfirmSelect,
    (85, 11): ConfirmSelectOk,
}

BINARY_HEADER_TO_METHOD = {
    b'\x00\x0A\x00\x3C': ConnectionBlocked,
    b'\x00\x0A\x00\x32': ConnectionClose,
    b'\x00\x0A\x00\x33': ConnectionCloseOk,
    b'\x00\x0A\x00\x28': ConnectionOpen,
    b'\x00\x0A\x00\x29': ConnectionOpenOk,
    b'\x00\x0A\x00\x0A': ConnectionStart,
    b'\x00\x0A\x00\x14': ConnectionSecure,
    b'\x00\x0A\x00\x0B': ConnectionStartOk,
    b'\x00\x0A\x00\x15': ConnectionSecureOk,
    b'\x00\x0A\x00\x1E': ConnectionTune,
    b'\x00\x0A\x00\x1F': ConnectionTuneOk,
    b'\x00\x0A\x00\x3D': ConnectionUnblocked,
    b'\x00\x14\x00\x28': ChannelClose,
    b'\x00\x14\x00\x29': ChannelCloseOk,
    b'\x00\x14\x00\x14': ChannelFlow,
    b'\x00\x14\x00\x15': ChannelFlowOk,
    b'\x00\x14\x00\x0A': ChannelOpen,
    b'\x00\x14\x00\x0B': ChannelOpenOk,
    b'\x00\x28\x00\x1E': ExchangeBind,
    b'\x00\x28\x00\x1F': ExchangeBindOk,
    b'\x00\x28\x00\x0A': ExchangeDeclare,
    b'\x00\x28\x00\x14': ExchangeDelete,
    b'\x00\x28\x00\x0B': ExchangeDeclareOk,
    b'\x00\x28\x00\x15': ExchangeDeleteOk,
    b'\x00\x28\x00\x28': ExchangeUnbind,
    b'\x00\x28\x00\x33': ExchangeUnbindOk,
    b'\x00\x32\x00\x14': QueueBind,
    b'\x00\x32\x00\x15': QueueBindOk,
    b'\x00\x32\x00\x0A': QueueDeclare,
    b'\x00\x32\x00\x28': QueueDelete,
    b'\x00\x32\x00\x0B': QueueDeclareOk,
    b'\x00\x32\x00\x29': QueueDeleteOk,
    b'\x00\x32\x00\x1E': QueuePurge,
    b'\x00\x32\x00\x1F': QueuePurgeOk,
    b'\x00\x32\x00\x32': QueueUnbind,
    b'\x00\x32\x00\x33': QueueUnbindOk,
    b'\x00\x3C\x00\x50': BasicAck,
    b'\x00\x3C\x00\x14': BasicConsume,
    b'\x00\x3C\x00\x1E': BasicCancel,
    b'\x00\x3C\x00\x15': BasicConsumeOk,
    b'\x00\x3C\x00\x1F': BasicCancelOk,
    b'\x00\x3C\x00\x3C': BasicDeliver,
    b'\x00\x3C\x00\x46': BasicGet,
    b'\x00\x3C\x00\x47': BasicGetOk,
    b'\x00\x3C\x00\x48': BasicGetEmpty,
    b'\x00\x3C\x00\x78': BasicNack,
    b'\x00\x3C\x00\x28': BasicPublish,
    b'\x00\x3C\x00\x0A': BasicQos,
    b'\x00\x3C\x00\x0B': BasicQosOk,
    b'\x00\x3C\x00\x32': BasicReturn,
    b'\x00\x3C\x00\x5A': BasicReject,
    b'\x00\x3C\x00\x64': BasicRecoverAsync,
    b'\x00\x3C\x00\x6E': BasicRecover,
    b'\x00\x3C\x00\x6F': BasicRecoverOk,
    b'\x00\x5A\x00\x14': TxCommit,
    b'\x00\x5A\x00\x15': TxCommitOk,
    b'\x00\x5A\x00\x1E': TxRollback,
    b'\x00\x5A\x00\x1F': TxRollbackOk,
    b'\x00\x5A\x00\x0A': TxSelect,
    b'\x00\x5A\x00\x0B': TxSelectOk,
    b'\x00\x55\x00\x0A': ConfirmSelect,
    b'\x00\x55\x00\x0B': ConfirmSelectOk,
}

CLASS_ID_TO_CONTENT_PROPERTY_LIST = {
    60: BasicContentPropertyList,
}

# Methods that are sent as replies to other methods, ie. ConnectionOpenOk: ConnectionOpen
# if a method is NOT a reply, it will not be in this dict
# a method may be a reply for AT MOST one method
REPLY_REASONS_FOR = {
    ConnectionCloseOk: ConnectionClose,
    ConnectionOpenOk: ConnectionOpen,
    ConnectionStartOk: ConnectionStart,
    ConnectionSecureOk: ConnectionSecure,
    ConnectionTuneOk: ConnectionTune,
    ChannelCloseOk: ChannelClose,
    ChannelFlowOk: ChannelFlow,
    ChannelOpenOk: ChannelOpen,
    ExchangeBindOk: ExchangeBind,
    ExchangeDeclareOk: ExchangeDeclare,
    ExchangeDeleteOk: ExchangeDelete,
    ExchangeUnbindOk: ExchangeUnbind,
    QueueBindOk: QueueBind,
    QueueDeclareOk: QueueDeclare,
    QueueDeleteOk: QueueDelete,
    QueuePurgeOk: QueuePurge,
    QueueUnbindOk: QueueUnbind,
    BasicConsumeOk: BasicConsume,
    BasicCancelOk: BasicCancel,
    BasicGetOk: BasicGet,
    BasicGetEmpty: BasicGet,
    BasicQosOk: BasicQos,
    TxCommitOk: TxCommit,
    TxRollbackOk: TxRollback,
    TxSelectOk: TxSelect,
    ConfirmSelectOk: ConfirmSelect,
}

# Methods that are replies for other, ie. ConnectionOpenOk: ConnectionOpen
# a method may be a reply for ONE or NONE other methods
# if a method has no replies, it will have an empty list as value here
REPLIES_FOR = {
    ConnectionBlocked: [],
    ConnectionClose: [ConnectionCloseOk],
    ConnectionCloseOk: [],
    ConnectionOpen: [ConnectionOpenOk],
    ConnectionOpenOk: [],
    ConnectionStart: [ConnectionStartOk],
    ConnectionSecure: [ConnectionSecureOk],
    ConnectionStartOk: [],
    ConnectionSecureOk: [],
    ConnectionTune: [ConnectionTuneOk],
    ConnectionTuneOk: [],
    ConnectionUnblocked: [],
    ChannelClose: [ChannelCloseOk],
    ChannelCloseOk: [],
    ChannelFlow: [ChannelFlowOk],
    ChannelFlowOk: [],
    ChannelOpen: [ChannelOpenOk],
    ChannelOpenOk: [],
    ExchangeBind: [ExchangeBindOk],
    ExchangeBindOk: [],
    ExchangeDeclare: [ExchangeDeclareOk],
    ExchangeDelete: [ExchangeDeleteOk],
    ExchangeDeclareOk: [],
    ExchangeDeleteOk: [],
    ExchangeUnbind: [ExchangeUnbindOk],
    ExchangeUnbindOk: [],
    QueueBind: [QueueBindOk],
    QueueBindOk: [],
    QueueDeclare: [QueueDeclareOk],
    QueueDelete: [QueueDeleteOk],
    QueueDeclareOk: [],
    QueueDeleteOk: [],
    QueuePurge: [QueuePurgeOk],
    QueuePurgeOk: [],
    QueueUnbind: [QueueUnbindOk],
    QueueUnbindOk: [],
    BasicAck: [],
    BasicConsume: [BasicConsumeOk],
    BasicCancel: [BasicCancelOk],
    BasicConsumeOk: [],
    BasicCancelOk: [],
    BasicDeliver: [],
    BasicGet: [BasicGetOk, BasicGetEmpty],
    BasicGetOk: [],
    BasicGetEmpty: [],
    BasicNack: [],
    BasicPublish: [],
    BasicQos: [BasicQosOk],
    BasicQosOk: [],
    BasicReturn: [],
    BasicReject: [],
    BasicRecoverAsync: [],
    BasicRecover: [],
    BasicRecoverOk: [],
    TxCommit: [TxCommitOk],
    TxCommitOk: [],
    TxRollback: [TxRollbackOk],
    TxRollbackOk: [],
    TxSelect: [TxSelectOk],
    TxSelectOk: [],
    ConfirmSelect: [ConfirmSelectOk],
    ConfirmSelectOk: [],
}
STRUCT_B = struct.Struct("!B")
STRUCT_HB = struct.Struct("!HB")
STRUCT_HH = struct.Struct("!HH")
STRUCT_BB = struct.Struct("!BB")
STRUCT_I = struct.Struct("!I")
STRUCT_L = struct.Struct("!L")
STRUCT_HIH = struct.Struct("!HIH")
STRUCT_2xB = struct.Struct("!2xB")
STRUCT_II = struct.Struct("!II")
STRUCT_QB = struct.Struct("!QB")
STRUCT_QBB = struct.Struct("!QBB")
STRUCT_IHB = struct.Struct("!IHB")
