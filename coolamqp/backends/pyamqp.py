"""Backend using pyamqp"""
import amqp
from .base import AMQPBackend

class PyAMQP(AMQPBackend):
    def __init__(self, host, user, password, virtual_host):
        self.amqp = amqp.Connection()