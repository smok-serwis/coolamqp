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
    def __init__(self, reply_code, reply_text, class_id, method_id):
        self.reply_code = reply_code
        self.reply_text = reply_text
        self.class_id = class_id
        self.method_id = method_id
