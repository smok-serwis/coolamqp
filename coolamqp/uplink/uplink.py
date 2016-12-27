# coding=UTF-8
from __future__ import absolute_import, division, print_function
import collections
from six.moves import queue


from coolamqp.uplink.frames.base_definitions import AMQPMethodPayload


class Uplink(object):
    """
    Uplink, the frame relay manager.

    It coordinates the joint effort of all the classes in this module.

    Uplink brings a thread to life - reader_thread - those job is to recv() on socket.



    There are two principal threads that can call Uplink.
    1) CoolAMQP frontend thread: this is the one processing events in the system. This thread
       is the only one allowed to send(), and will frequently block on it.

       Well, you can't process more tasks if you are hanging on send, are you.

    2) Reader thread, spawned and managed by Uplink. This is the thread running recv() on the socket,
       calling the callbacks that you register, and so on.

    """

    def __init__(self):
        #                       Watchers
        # Watcher is a one-time trigger set on one (or more) method frames.
        self.watchers_to_register = queue.Queue()
        pass



    def listen_for_method_frame(self, frames, on_frame=lambda f: None, on_dead=None):
        """
        Register a one-time listener for a particular method frame (or may kinds of frame).

        When one matching frame arrives, on_frame will be called and rest of subscriptions will be evicted.

        The callback will be executed in Uplink's internal thread context.

        :param frames:
        :param on_frame:
        :param on_dead:
        :return:
        """

    def



    def on_socket_failed(self, exc):
        """Called by ReaderThread when it detects that socket has failed"""