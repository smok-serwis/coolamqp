# coding=UTF-8
from __future__ import absolute_import, division, print_function


from coolamqp.backends.base import AMQPBackend


# Create a global ListenerThread
from coolamqp.uplink import ListenerThread
GLOBALS = {
    'listener': ListenerThread()
}


class CoolAMQPBackend(AMQPBackend):
    """
    A backend utilizing CoolAMQP's coolamqp.attaches and coolamqp.connection.
    Backend starts with creating a connection, and ends with blanging it.
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

    def basic_consume(self, queue, no_ack=False):
        """
        Start consuming from a queue
        :param queue: Queue object
        :param no_ack: Messages will not need to be ack()ed for this queue
        """

    def basic_ack(self, delivery_tag):
        """
        ACK a message.
        :param delivery_tag: delivery tag to ack
        """

    def basic_qos(self, prefetch_size, prefetch_count, global_):
        """
        Issue a basic.qos(prefetch_size, prefetch_count, True) against broker
        :param prefetch_size: prefetch window size in octets
        :param prefetch_count: prefetch window in terms of whole messages
        """

    def basic_reject(self, delivery_tag):
        """
        Reject a message
        :param delivery_tag: delivery tag to reject
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
        This is not allowed to return anything or raise
        """
        self.cluster_handler_thread = None  # break GC cycles
