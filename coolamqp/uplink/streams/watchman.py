# coding=UTF-8
from __future__ import absolute_import, division, print_function
import collections
from six.moves import queue


class Watchman(object):
    """
    Watchman is a guy that you can:

     - If you are ReaderThread, ask "hey, this frame just arrived,
     is someone interested in it?"
     - If you are frontend thread, can ask watchman to trigger a callback
     when a particular frame arrives (or a bunch of them, if your request
     expects a bunch).

    Since Watchman receives all frames from ReaderThread, it also knows about:
    - channels being opened
    - channels being closed by exception
    -

     Watchman is also being informed about new channels being opened

        See page 19 of the AMQP specification. Responses for synchronous methods
        arrive in order, ie. if I requested a queue.declare, and then an
        exchange.declare, I expect that responses will arrive in order of
        queue.declare-ok, exchange.declare-ok.

        This is important, because if we have a message, we need to check only
        the first watch.

        :FRAMES = [AMQPMethodPayloadClass1, AMQPMethodPayloadClass2, ...]
        :ONFRAME = callable(AMQPMethodPayload instance)
        :ONDEAD = callable() | None

        :WATCH = ( :FRAMES :ONFRAME :ONDEAD )
        :WATCH_TO_LOAD = ( channel :FRAMES :ONFRAME :ONDEAD)


        !!!!! LIMITED RIGHT NOW ONLY TO METHOD FRAMES
    """
    def __init__(self):
        self.watches_to_load = queue.Queue()    # put new watches here

        self.watches = {}   # channel => list of :WATCH



    def _analyze_watches(self):

    def on_frame(self, frame):
        """
        A frame arrived. If this triggers a watch, trigger it and remove.
        All frames received by ReaderThread go thru here.

        TO BE CALLED BY READER THREAD

        :param frame: AMQPFrame of any subtype
        """

        # Analyze pending watches
        while self.watches_to_load.qsize() > 0:
            channel,


    def set_watch(self, channel, frame_types, on_frame, on_dead=None):
        """
        Set a watch. Watch will fire if I see a method frame of type
        found in the iterable of frame_types.

        TO BE CALLED BY FRONTEND THREAD.

        :param channel: channel to set watch on
        :param frame_types: list of AMQPMethodPayload classes
        :param on_frame: callable(AMQPMethodPayload instance)
        :param on_dead: callable/0 to call if this watch will
            for sure not be processed (eg. channel or connection died)
        """
        self.watches_to_load.put((channel, frame_types, on_frame, on_dead))
        if channel not in self.watches:
            p = collections.deque((frame_types, on_frame, on_dead))
            self.watches[channel] = p
        else:
            self.watches[channel].put
