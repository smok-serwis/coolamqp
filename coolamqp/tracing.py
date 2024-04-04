import logging

from coolamqp.framing.frames import AMQPMethodFrame


class BaseFrameTracer(object):
    """An abstract do-nothing frame tracer"""

    def on_frame(self, timestamp, frame, direction):
        """
        Called by AMQP upon receiving a frame information

        :param timestamp: timestamp
        :type timestamp: float
        :param frame: frame that is sent or received
        :type frame: :class:`coolamqp.framing.base.AMQPFrame`
        :param direction: either 'to_client' or 'to_server'
        :type direction: str
        """


class LoggingFrameTracer(BaseFrameTracer):
    """
    A frame tracer that outputs each frame to log

    :param logger: the logger to log onto (defaults to logging.getLogger(__name__))
    :param log_level: the level of logging to log with
    """
    def __init__(self, logger=None, log_level=logging.WARNING):
        self.logger = logger or logging.getLogger(__name__)
        self.log_level = log_level

    def on_frame(self, timestamp, frame, direction):
        if direction == 'to_client':
            if isinstance(frame, AMQPMethodFrame):
                self.logger.log(self.log_level, 'RECEIVED METHOD %s', frame.payload)
            else:
                self.logger.log(self.log_level, 'RECEIVED %s type %s', frame, type(frame))
        else:
            if isinstance(frame, AMQPMethodFrame):
                self.logger.log(self.log_level, 'SENT METHOD %s', frame.payload)
            else:
                self.logger.log(self.log_level, 'SENT %s type %s', frame, type(frame))


class HoldingFrameTracer(BaseFrameTracer):
    """
    A frame tracer that holds the frames in memory

    :ivar frames: a list of tuple (direction:str (either 'to_client' or 'to_server'),
                              timestamp::float,
                              frame:: :class:`~coolamqp.framing.base.AMQPFrame`)
    """
    def __init__(self):
        self.frames = []

    def on_frame(self, timestamp, frame, direction):
        self.frames.append((direction, timestamp, frame))

    def clear(self):
        """Clear internal frame list"""
        self.frames = []
