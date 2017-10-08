# coding=UTF-8
from __future__ import print_function, absolute_import
"""
A Python version of the AMQP machine-readable specification.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See coolamqp.uplink.framing.compilation for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016 DMS Serwis s.c.


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

import struct, collections, logging, six

from coolamqp.framing.base import AMQPClass, AMQPMethodPayload, AMQPContentPropertyList
from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size
from coolamqp.framing.compilation.content_property import compile_particular_content_property_list_class

logger = logging.getLogger(__name__)

Field = collections.namedtuple('Field', ('name', 'type', 'basic_type', 'reserved'))

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

REPLY_SUCCESS = 200
REPLY_SUCCESS_BYTE = b'\xc8'
 # Indicates that the method completed successfully. This reply code is
                              # reserved for future use - the current protocol design does not use
                              # positive
                              # confirmation and reply codes are sent only in case of an error.
CONTENT_TOO_LARGE = 311
 # The client attempted to transfer content larger than the server
                         # could accept
                         # at the present time. The client may retry at a later time.
NO_CONSUMERS = 313
 # When the exchange cannot deliver to a consumer when the immediate
                    # flag is
                    # set. As a result of pending data on the queue or the absence of any
                    # consumers of the queue.
CONNECTION_FORCED = 320
 # An operator intervened to close the connection for some reason. The
                         # client
                         # may retry at some later date.
INVALID_PATH = 402
 # The client tried to work with an unknown virtual host.
ACCESS_REFUSED = 403
 # The client attempted to work with a server entity to which it has no
                      # access due to security settings.
NOT_FOUND = 404
 # The client attempted to work with a server entity that does not
                 # exist.
RESOURCE_LOCKED = 405
 # The client attempted to work with a server entity to which it has no
                       # access because another client is working with it.
PRECONDITION_FAILED = 406
 # The client requested a method that was not allowed because some
                           # precondition
                           # failed.
FRAME_ERROR = 501
 # The sender sent a malformed frame that the recipient could not
                   # decode.
                   # This strongly implies a programming error in the sending peer.
SYNTAX_ERROR = 502
 # The sender sent a frame that contained illegal values for one or
                    # more
                    # fields. This strongly implies a programming error in the sending
                    # peer.
COMMAND_INVALID = 503
 # The client sent an invalid sequence of frames, attempting to perform
                       # an
                       # operation that was considered invalid by the server. This usually
                       # implies
                       # a programming error in the client.
CHANNEL_ERROR = 504
 # The client attempted to work with a channel that had not been
                     # correctly
                     # opened. This most likely indicates a fault in the client layer.
UNEXPECTED_FRAME = 505
 # The peer sent a frame that was not expected, usually in the context
                        # of
                        # a content header and body. This strongly indicates a fault in the
                        # peer's
                        # content processing.
RESOURCE_ERROR = 506
 # The server could not complete the method because it lacked
                      # sufficient
                      # resources. This may be due to the client creating too many of some
                      # type
                      # of entity.
NOT_ALLOWED = 530
 # The client tried to work with some entity in a manner that is
                   # prohibited
                   # by the server, due to security settings or by some other criteria.
NOT_IMPLEMENTED = 540
 # The client tried to use functionality that is not implemented in the
                       # server.
INTERNAL_ERROR = 541
 # The server could not complete the method because of an internal
                      # error.
                      # The server may require intervention by an operator in order to
                      # resume
                      # normal operations.

HARD_ERRORS = [CONNECTION_FORCED, INVALID_PATH, FRAME_ERROR, SYNTAX_ERROR, COMMAND_INVALID, CHANNEL_ERROR, UNEXPECTED_FRAME, RESOURCE_ERROR, NOT_ALLOWED, NOT_IMPLEMENTED, INTERNAL_ERROR]
SOFT_ERRORS = [CONTENT_TOO_LARGE, NO_CONSUMERS, ACCESS_REFUSED, NOT_FOUND, RESOURCE_LOCKED, PRECONDITION_FAILED]


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
