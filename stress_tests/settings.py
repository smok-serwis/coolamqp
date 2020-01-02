import logging

from coolamqp.clustering import Cluster
from coolamqp.objects import NodeDefinition

logger = logging.getLogger(__name__)

NODE = NodeDefinition('127.0.0.1', 'guest', 'guest', heartbeat=20)
logging.basicConfig(level=logging.DEBUG)


def connect(**kwargs):
    amqp = Cluster([NODE], **kwargs)
    amqp.start(wait=True)
    return amqp


queue_names = (str(v) for v in range(1000))
