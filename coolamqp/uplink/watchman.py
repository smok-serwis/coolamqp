# coding=UTF-8
from __future__ import absolute_import, division, print_function
import collections
from six.moves import queue


from coolamqp.uplink.exceptions import called_by
from coolamqp.scaffold import AcceptsFrames, RelaysFrames, Synchronized

from coolamqp.framing.frames import AMQPMethodFrame, AMQPHeartbeatFrame, AMQPBodyFrame, AMQPHeaderFrame


class Watch(object):
    def __init__(self, channel, on_frame, predicate):
        """
        :type predicate: callable(AMQPFrame object) -> should_trigger::bool
        """
        self.channel = channel
        self.on_frame = on_frame
        self.predicate = predicate




class Watchman(AcceptsFrames, RelaysFrames, Synchronized):
    """
    Watchman is the guy, who:

    - Receives frames from RecvFramer
    - Executes in the context of the Listener
    - You can ask to trigger, when a particular frame is received from server
    """

    def __init__(self):
        super(Watchman, self).__init__(self)
        self.watches = collections.defaultdict(collections.deque)
        self.on_frame = lambda frame: None

    def wire_frame_to(self, on_frame):
        """
        Set this Watchman to pass non-triggered frames to some callable.

        Called by: Uplink factory

        :param callable: callable(AMQPMethodPayload object)
        """
        self.on_frame = on_frame

    @
    def trigger_methods(self, channel, frame_payload_types, on_frame):
        """
        Register a one-shot trigger on an AMQP method.

        After triggering upon any of method frame payload types, you'll get a callback with
        AMQPMethodPayload instance. This will prevent it from being relayed further.

        Called by: frontend, listener

        :param channel: channel ID
        :param frame_payload_types: list of AMQPMethodPayload classes
        :param on_frame: callable(AMQPMethodPayload instance) -> n/a
        """
        def predicate(frame):
            if not isinstance(frame, )
        m = Watch(channel, on_frame, lambda frame: isinstance(frame.payload ))
        with self.lock:




     - If you are ReaderThread, ask "hey, this frame just arrived,
     is someone interested in it?"
     - If you are frontend thread, can ask watchman to trigger a callback
     when a particular frame arrives (or a bunch of them, if your request
     expects a bunch).

    Since Watchman receives all framing from ReaderThread, it also knows about:
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
        All framing received by ReaderThread go thru here.

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
