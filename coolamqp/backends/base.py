

class AMQPError(Exception):
    pass


class ConnectionFailedError(AMQPError):
    """Connection to broker failed"""

class RemoteAMQPError(AMQPError):
    """
    Remote AMQP broker responded with an error code
    """
    def __init__(self, code, text=None):
        """
        :param code: AMQP error code
        :param text: AMQP error text (optional)
        """
        AMQPError.__init__(self, text)
        self.code = code


class AMQPBackend(object):
    """
    Dummy AMQP backend.

    Every method may raise either ConnectionFailedError (if connection failed)
    or RemoteAMQPError (if broker returned an error response)
    """

    def __init__(self, cluster_node, cluster_handler_thread):
        """
        Connects to an AMQP backend.
        """
        self.cluster_handler_thread = cluster_handler_thread

    def process(self, max_time=10):
        """
        Do bookkeeping, process messages, etc.
        :param max_time: maximum time in seconds this call can take
        :raises ConnectionFailedError: if connection failed in the meantime
        """

    def exchange_declare(self, exchange):
        """
        Declare an exchange
        :param exchange: Exchange object
        """

    def exchange_delete(self, exchange):
        """
        Delete an exchange
        :param exchange: Exchange object
        """

    def queue_bind(self, queue, exchange, routing_key=''):
        """
        Bind a queue to an exchange
        :param queue: Queue object
        :param exchange: Exchange object
        :param routing_key: routing key to use
        """

    def queue_delete(self, queue):
        """
        Delete a queue.

        :param queue: Queue
        """


    def queue_declare(self, queue):
        """
        Declare a queue.

        This will change queue's name if anonymous
        :param queue: Queue
        """

    def basic_cancel(self, consumer_tag):
        """
        Cancel consuming, identified by a consumer_tag
        :param consumer_tag: consumer_tag to cancel
        """

    def basic_consume(self, queue):
        """
        Start consuming from a queue
        :param queue: Queue object
        """

    def basic_ack(self, delivery_tag):
        """
        ACK a message.
        :param delivery_tag: delivery tag to ack
        """

    def basic_qos(self, prefetch_size, prefetch_count):
        """
        Issue a basic.qos(prefetch_size, prefetch_count, True) against broker
        :param prefetch_size: prefetch window size in octets
        :param prefetch_count: prefetch window in terms of whole messages
        """

    def basic_nack(self, delivery_tag):
        """
        NACK a message.
        :param delivery_tag: delivery tag to nack
        """

    def basic_publish(self, message, exchange, routing_key):
        """
        Send a message
        :param message: Message object to send
        :param exchange: Exchange object to publish to
        :param routing_key: routing key to use
        """

    def shutdown(self):
        """
        Close this connection.
        This is not allowed to return anything.
        """
        self.cluster_handler_thread = None  # break GC cycles
