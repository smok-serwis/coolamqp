import logging
import os

from coolamqp.clustering import Cluster
from coolamqp.objects import NodeDefinition

logger = logging.getLogger(__name__)

NODE = NodeDefinition(os.environ.get('AMQP_HOST', 'rabbitmq'), 'guest', 'guest', heartbeat=20)
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
        try:
            self.file.write('%s %s %s\n' % (timestamp, frame, direction))
            self.file.flush()
        except ValueError:
            pass

queue_names = (str(v) for v in range(100))
