# coding=UTF-8
from __future__ import absolute_import, division, print_function


class CoolAMQPError(Exception):
    """Base class for CoolAMQP errors"""



class ConsumerError(CoolAMQPError):
    """
    Exceptions passed to consumer callables.
    """


class UplinkLost(ConsumerError):
    """
    Uplink to the network has been lost, I am working on regaining connectivity
    right now.
    """

class ConsumerCancelled(CoolAMQPError):
    """
    The consumer has been cancelled
    """


class AMQPError(CoolAMQPError):
    """
    Base class for errors received from AMQP server
    """
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


class ResourceLocked(AMQPError):
    """Shorthand to catch that stuff easier"""
