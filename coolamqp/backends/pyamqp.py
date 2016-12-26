# coding=UTF-8
"""Backend using pyamqp"""
from __future__ import division
import amqp
import socket
import six
import functools
import logging
from coolamqp.backends.base import AMQPBackend, RemoteAMQPError, ConnectionFailedError
import monotonic


logger = logging.getLogger(__name__)


def translate_exceptions(fun):
    """
    Translates pyamqp's exceptions to CoolAMQP's

    py-amqp's exceptions are less than intuitive, so expect many special cases
    """
    @functools.wraps(fun)
    def q(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except (amqp.exceptions.ConsumerCancelled):
            # I did not expect those here. Channel must be really bad.
            logger.critical('Found consumer cancelled where it should not be')
            raise ConnectionFailedError('WTF: '+(e.message if six.PY2 else e.args[0]))
        except (amqp.RecoverableChannelError,
                amqp.exceptions.NotFound,
                amqp.exceptions.NoConsumers,
                amqp.exceptions.ResourceLocked,
                amqp.exceptions.ResourceError,
                amqp.exceptions.ResourceLocked,
                amqp.exceptions.AccessRefused) as e:
            logger.warn('py-amqp: backend reports %s:%s', e.reply_code, e.reply_text)
            raise RemoteAMQPError(e.reply_code, e.reply_text)
        except (IOError,
                amqp.ConnectionForced,
                amqp.exceptions.InvalidPath,
                amqp.IrrecoverableChannelError,
                amqp.exceptions.UnexpectedFrame) as e:
            logger.warn('py-amqp: backend reports %s:%s', e.reply_code, e.reply_text)
            raise ConnectionFailedError(e.message if six.PY2 else e.args[0])
    return q


class PyAMQPBackend(AMQPBackend):
    @translate_exceptions
    def __init__(self, node, cluster_handler_thread):
        AMQPBackend.__init__(self, node, cluster_handler_thread)

        self.connection = amqp.Connection(host=node.host,
                                          userid=node.user,
                                          password=node.password,
                                          virtual_host=node.virtual_host,
                                          heartbeat=node.heartbeat or 0)
        try:
            self.connection.connect()     #todo what does this raise?
        except AttributeError:
            pass    # this does not always have to exist
        self.channel = self.connection.channel()
        self.channel.auto_decode = False
        self.heartbeat = node.heartbeat or 0
        self.last_heartbeat_at = monotonic.monotonic()

    def shutdown(self):
        AMQPBackend.shutdown(self)
        print 'BACKEND SHUTDOWN START'
        try:
            self.channel.close()
        except:
            pass
        try:
            self.connection.close()
        except:
            pass
        print 'BACKEND SHUTDOWN COMPLETE'

    @translate_exceptions
    def process(self, max_time=1):
        try:
            if self.heartbeat > 0:
                if monotonic.monotonic() - self.last_heartbeat_at > (self.heartbeat / 2):
                    self.connection.heartbeat_tick(rate=self.heartbeat)
                    self.last_heartbeat_at = monotonic.monotonic()
            self.connection.drain_events(max_time)
        except socket.timeout as e:
            pass

    @translate_exceptions
    def basic_cancel(self, consumer_tag):
        self.channel.basic_cancel(consumer_tag)

    @translate_exceptions
    def basic_publish(self, message, exchange, routing_key):
        # convert this to pyamqp's Message
        a = amqp.Message(six.binary_type(message.body),
                         **message.properties)

        self.channel.basic_publish(a, exchange=exchange.name, routing_key=routing_key)

    @translate_exceptions
    def exchange_declare(self, exchange):
        self.channel.exchange_declare(exchange.name, exchange.type, durable=exchange.durable,
                                      auto_delete=exchange.auto_delete)

    @translate_exceptions
    def queue_bind(self, queue, exchange, routing_key=''):
        self.channel.queue_bind(queue.name, exchange.name, routing_key)

    @translate_exceptions
    def basic_ack(self, delivery_tag):
        self.channel.basic_ack(delivery_tag, multiple=False)

    @translate_exceptions
    def exchange_delete(self, exchange):
        self.channel.exchange_delete(exchange.name)

    @translate_exceptions
    def basic_qos(self, prefetch_size, prefetch_count, global_):
        self.channel.basic_qos(prefetch_size, prefetch_count, global_)

    @translate_exceptions
    def queue_delete(self, queue):
        self.channel.queue_delete(queue.name)

    @translate_exceptions
    def basic_reject(self, delivery_tag):
        self.channel.basic_reject(delivery_tag, True)

    @translate_exceptions
    def queue_declare(self, queue):
        """
        Declare a queue.

        This will change queue's name if anonymous
        :param queue: Queue
        """
        if queue.anonymous:
            queue.name = ''

        qname, mc, cc = self.channel.queue_declare(queue.name,
                                                   durable=queue.durable,
                                                   exclusive=queue.exclusive,
                                                   auto_delete=queue.auto_delete)
        if queue.anonymous:
            queue.name = qname

    @translate_exceptions
    def basic_consume(self, queue, no_ack=False):
        """
        Start consuming from a queue
        :param queue: Queue object
        """
        self.channel.basic_consume(queue.name,
                                   consumer_tag=queue.consumer_tag,
                                   exclusive=queue.exclusive,
                                   no_ack=no_ack,
                                   callback=self.__on_message,
                                   on_cancel=self.__on_consumercancelled)

    def __on_consumercancelled(self, consumer_tag):
        self.cluster_handler_thread._on_consumercancelled(consumer_tag)

    def __on_message(self, message):
        assert isinstance(message.body, six.binary_type)
        self.cluster_handler_thread._on_recvmessage(message.body,
                                                    message.delivery_info['exchange'],
                                                    message.delivery_info['routing_key'],
                                                    message.delivery_info['delivery_tag'],
                                                    message.properties)
