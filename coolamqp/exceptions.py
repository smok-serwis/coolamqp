# coding=UTF-8
from __future__ import absolute_import, division, print_function

from coolamqp.framing.definitions import HARD_ERRORS, RESOURCE_LOCKED


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

    def __str__(self):
        return u'AMQP error %s: %s' % (self.reply_code, self.reply_text)

    def __repr__(self):
        return u'AMQPError(%s, %s, %s, %s)' % (
            repr(self.reply_code),
            repr(self.reply_text),
            repr(self.class_id),
            repr(self.method_id),
        )

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
