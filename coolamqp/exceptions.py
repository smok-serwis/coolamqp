# coding=UTF-8
from __future__ import absolute_import, division, print_function

from coolamqp.framing.definitions import HARD_ERRORS, SOFT_ERRORS, CONNECTION_FORCED, INVALID_PATH, FRAME_ERROR, \
    SYNTAX_ERROR, COMMAND_INVALID, CHANNEL_ERROR, UNEXPECTED_FRAME, RESOURCE_ERROR, NOT_ALLOWED, NOT_IMPLEMENTED, \
    INTERNAL_ERROR, CONTENT_TOO_LARGE, NO_CONSUMERS, ACCESS_REFUSED, NOT_FOUND, RESOURCE_LOCKED, PRECONDITION_FAILED


class CoolAMQPError(Exception):
    """Base class for CoolAMQP errors"""


class ConnectionDead(CoolAMQPError):
    """
    Operation could be not completed because some other error
    than a legit AMQPError occurred, such as exploding kitten
    """


class AMQPError(CoolAMQPError):
    """
    Base class for errors received from AMQP server
    """

    def is_hard_error(self):
        """Does this error close the connection?"""
        return self.reply_code in HARD_ERRORS

    def __init__(self, *args):
        """

        :param args: can be either reply_code, reply_text, class_id, method_id
                     or a ConnectionClose/ChannelClose.
        """
        from coolamqp.framing.definitions import ConnectionClose, ChannelClose

        if isinstance(args[0], (ConnectionClose, ChannelClose)):
            self.reply_code = args[0].reply_code
            self.reply_text = args[0].reply_text
            self.class_id = args[0].class_id
            self.method_id = args[0].method_id
        else:
            assert len(args) == 4
            self.reply_code, self.reply_text, self.class_id, self.method_id = args
