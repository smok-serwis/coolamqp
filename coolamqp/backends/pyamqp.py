"""Backend using pyamqp"""
import amqp
import functools
from .base import AMQPBackend, AMQPError, RemoteAMQPError, ConnectionFailedError


def translate_exceptions(fun):
    """Translates pyamqp's exceptions to CoolAMQP's"""
    @functools.wraps(fun)
    def q(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except amqp.ChannelError as e:
            raise RemoteAMQPError(e.reply_code, e.reply_text)
        except IOError as e:
            raise ConnectionFailedError
    return q


class PyAMQPBackend(AMQPBackend):
    def __init__(self, node, cluster_handler_thread):
        AMQPBackend.__init__(self, cluster_handler_thread)

        self.connection = amqp.Connection(host=node.host,
                                          userid=node.user,
                                          password=node.password,
                                          virtual_host=node.virtual_host)
        self.connection.connect()     #todo what does this raise?
        self.channel = self.connection.channel()

    def shutdown(self):
        AMQPBackend.shutdown(self)
        try:
            self.channel.close()
        except:
            pass
        try:
            self.connection.close()
        except:
            pass

    @translate_exceptions
    def process(self, max_time=10):
        self.connection.heartbeat_tick()
        self.connection.drain_events(max_time)

    @translate_exceptions
    def basic_cancel(self, consumer_tag):
        self.amqp_channel.basic_cancel(consumer_tag)

    @translate_exceptions
    def basic_publish(self, message, exchange, routing_key):
        # convert this to pyamqp's Message
        a = amqp.Message(message.body,
                         **message.properties)

        self.amqp_channel.basic_publish(a, exchange=exchange.name, routing_key=routing_key)

    @translate_exceptions
    def exchange_declare(self, exchange):
        self.channel.exchange_declare(exchange.name, exchange.type, durable=exchange.durable,
                                      auto_delete=exchange.auto_delete)

    @translate_exceptions
    def queue_bind(self, queue, exchange, routing_key=''):
        self.channel.queue_bind(queue.name, exchange.name, routing_key)

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
    def basic_consume(self, queue,  on_message, on_cancel):
        """
        Start consuming from a queue
        :param queue: Queue object
        :param on_message: callable/1
        """
        self.channel.basic_consume(queue.name,
                                   consumer_tag=queue.consumer_tag,
                                   exclusive=queue.exclusive,
                                   callback=self.__on_message,
                                   on_cancel=self.__on_consumercancelled)

    def __on_consumercancelled(self, consumer_tag):
        self.cluster_handler_thread._on_consumercancelled(consumer_tag)

    def __on_message(self, message):
        self.cluster_handler_thread._on_recvmessage(message.body,
                                                    message.delivery_info['exchange'],
                                                    message.delivery_info['routing_key'],
                                                    message.delivery_info['delivery_tag'],
                                                    message.properties)

