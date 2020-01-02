import logging

from coolamqp.clustering import Cluster
from coolamqp.objects import NodeDefinition

logger = logging.getLogger(__name__)

NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


def connect(on_fail=lambda: None, log_frames=None):
    def _on_fail():
        on_fail.put('fail')

    amqp = Cluster([NODE], on_fail=_on_fail, log_frames=log_frames)
    amqp.start(wait=True)
    return amqp


class LogFramesToFile:
    def __init__(self, path):
        self.file = open(path, 'w')

    def close(self):
        self.file.close()

    def on_frame(self, timestamp, frame, direction):
        self.file.write('%s %s %s\n' % (timestamp, frame, direction))
        self.file.flush()


queue_names = (str(v) for v in range(2))
