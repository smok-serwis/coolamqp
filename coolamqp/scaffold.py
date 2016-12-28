# coding=UTF-8
"""
Utilities for building the CoolAMQP engine
"""
from __future__ import absolute_import, division, print_function
import functools
import threading


class Synchronized(object):
    """Protects access to methods with a lock"""
    def __init__(self):
        self.lock = threading.Lock()

    def protect(self):
        """Make the function body lock-protected"""
        def outer(fun):
            @functools.wraps(fun)
            def inner(*args, **kwargs):
                with self.lock:
                    return fun(*args, **kwargs)
            return inner
        return outer


class AcceptsFrames(object):
    """Base class for objects that accept AMQP frames"""

    def on_frame(self, amqp_frame):
        """
        :type amqp_frame: AMQPFrame object
        """


class EmitsFrames(object):
    """Base class for objects that send AMQP frames somewhere"""

    def wire_frame_to(self, acceptor):
        """
        Configure this object to send frames somewhere.

        :param acceptor: an AcceptsFrames instance or callable(AMQPMethod instance)
        """