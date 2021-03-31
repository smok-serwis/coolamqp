import logging


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

    :param logger: the logger to log onto
    :param log_level: the level of logging to log with
    """
    def __init__(self, logger, log_level=logging.WARNING):
        self.logger = logger
        self.log_level = log_level

    def on_frame(self, timestamp, frame, direction):
        if direction == 'to_client':
            self.logger.log(self.log_level, 'RECEIVED %s', frame.payload)
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
