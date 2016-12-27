# coding=UTF-8
from __future__ import absolute_import, division, print_function



class MethodTransaction(object):
    """
    This means "run a method, and call me back when reply arrives".

    Method's
    """


class SyncOrder(Order):
    """
    This means "send a method frame, optionally some other frames,
    and run a callback with the returned thing.

    Possible responses are registered for.
    """
    def __init__(self, channel, method, other_frames=[], callback=lambda frame: None):
        """
        :param channel: channel to use
        :param method: AMQPMethodPayload instance
        :param other_frames: list of other AMQPFrames to send next in order
        :param callback: callback to run with received response.
            methods that this will react to are determined by AMQPMethodPayload
        """


