import itertools
import Queue
from coolamqp.backends import PyAMQPBackend
from .orders import SendMessage


class ClusterNode(object):
    """
    Definition of a reachable AMQP node.

    This object is hashable.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a cluster node definition.

            a = ClusterNode(host='192.168.0.1', user='admin', password='password',
                            vhost='vhost')
        """

        if len(kwargs) == 0:
            # Prepare arguments for amqp.connection.Connection
            self.host = kwargs['host']
            self.user = kwargs['user']
            self.password = kwargs['password']
            self.virtual_host = kwargs.get('virtual_host', '/')
        else:
            raise NotImplementedError #todo implement this

    def __str__(self):
        return '%s@%s/%s' % (self.host,
                             self.user,
                             self.virtual_host)



class Cluster(object):
    """
    Represents connection to an AMQP cluster. This internally connects only to one node.
    """

    def __init__(self, nodes, backend=PyAMQPBackend):
        """
        Construct the cluster definition
        :param nodes: iterable of nodes to try connecting, in this order.
            if list if exhaused, it will be started from beginning
        :param backend: backend to use
        """

        self.backend = backend
        self.node_to_connect_to = itertools.cycle(nodes)\

        from .handler import ClusterHandlerThread
        self.thread = ClusterHandlerThread(self)

    def send(self, message, exchange, routing_key, on_completed=None, on_failed=None):
        """
        Schedule a message to be sent.
        :param message: Message object to send
        :param exchange: Exchange to use
        :param routing_key: routing key to use
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        """
        self.thread.order_queue.append(SendMessage(message, exchange, routing_key,
                                                   on_completed=on_completed,
                                                   on_failed=on_failed))

    def declare_exchange(self, exchange, on_completed=None, on_failed=None):
        """
        Declare an exchange
        :param exchange: Exchange to declare
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        """

    def consume(self, queue):
        """
        Start consuming from a queue

        This queue will be declared to the broker. If this queue has any binds
        (.exchange field is not empty), queue will be binded to exchanges.

        :param queue: Queue to consume from.
        :return:
        """


    def drain(self, wait=0):
        """
        Return a ClusterEvent on what happened, or None if nothing could be obtained
        within given time
        :param wait: Interval to wait for events.
            Finite number to wait this much seconds before returning None
            None to wait for infinity
            0 to return immediately
        :return: a ClusterEvent instance or None
        """

        if wait == 0:
            try:
                return self.thread.event_queue.get(False)
            except Queue.Empty:
                return None
        else:
            return self.thread.event_queue.get(True, wait)

    def start(self):
        """
        Connect to the cluster.
        :return: self
        """
        self.thread.start()
        return self

    def shutdown(self):
        """
        Cleans everything and returns
        """
        self.thread.terminate()
        self.thread.join()
        return