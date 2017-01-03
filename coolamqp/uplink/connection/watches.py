# coding=UTF-8
from __future__ import absolute_import, division, print_function

from coolamqp.framing.frames import AMQPMethodFrame, AMQPHeartbeatFrame


class Watch(object):
    """
    A watch is placed per-channel, to listen for a particular frame.
    """

    def __init__(self, channel, oneshot):
        """
        :param channel: Channel to listen to
        :param oneshot: Is destroyed after triggering?
        """
        self.channel = channel
        self.oneshot = oneshot
        self.cancelled = False

    def is_triggered_by(self, frame):
        """
        Does frame trigger this watch?
        Run callable if it does.
        :param frame: AMQPFrame instance
        :return: bool
        """
        raise Exception('Abstract method')

    def failed(self):
        """
        This watch will process things no more, because underlying
        link has failed
        """

    def cancel(self):
        """
        Called by watch's user. This watch will not receive events anymore
        (whether about frame or fail), and it will be discarded upon next iteration.
        """
        self.cancelled = True


class FailWatch(Watch):
    """
    A special kind of watch that fires when connection has died
    """
    def __init__(self, callable):
        Watch.__init__(self, None, True)
        self.callable = callable

    def fire(self):
        """
        Connection failed!
        """
        self.callable()


class HeartbeatWatch(Watch):
    """
    Registered if heartbeats are enabled
    """
    def __init__(self, callable):
        Watch.__init__(self, 0, False)
        self.callable = callable

    def is_triggered_by(self, frame):
        if isinstance(frame, AMQPHeartbeatFrame):
            self.callable()
            return True
        return False


class MethodWatch(Watch):
    """
    One-shot watch listening for methods.
    """
    def __init__(self, channel, method_or_methods, callable, on_end=None):
        """
        :param method_or_methods: class, or list of AMQPMethodPayload classes
        :param callable: callable(AMQPMethodPayload instance)
        :param on_end: callable/0 on link dying
        """
        Watch.__init__(self, channel, True)
        self.callable = callable
        if isinstance(method_or_methods, (list, tuple)):
            self.methods = tuple(method_or_methods)
        else:
            self.methods = method_or_methods
        self.on_end = on_end

    def failed(self):
        if self.on_end is not None:
            self.on_end()

    def is_triggered_by(self, frame):

        if not isinstance(frame, AMQPMethodFrame):
            return False

        if isinstance(frame.payload, self.methods):
            self.callable(frame.payload)
            return True
        return False
