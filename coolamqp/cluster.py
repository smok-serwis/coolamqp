#coding=UTF-8
import itertools
from six.moves import queue as Queue
from coolamqp.backends import PyAMQPBackend
from .orders import SendMessage, ConsumeQueue, DeclareExchange, CancelQueue, DeleteQueue, \
                    DeleteExchange, SetQoS, DeclareQueue
from .messages import Exchange


class ClusterNode(object):
    """
    Definition of a reachable AMQP node.

    This object is hashable.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a cluster node definition.

            a = ClusterNode(host='192.168.0.1', user='admin', password='password',
                            virtual_host='vhost')

        or

            a = ClusterNode('192.168.0.1', 'admin', 'password')

        Additional keyword parameters that can be specified:
            heartbeat - heartbeat interval in seconds
        """

        self.heartbeat = kwargs.pop('heartbeat', None)

        if len(kwargs) > 0:
            # Prepare arguments for amqp.connection.Connection
            self.host = kwargs['host']
            self.user = kwargs['user']
            self.password = kwargs['password']
            self.virtual_host = kwargs.get('virtual_host', '/')
        elif len(args) == 3:
            self.host, self.user, self.password = args
            self.virtual_host = '/'
        elif len(args) == 4:
            self.host, self.user, self.password, self.virtual_host = args
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
        self.node_to_connect_to = itertools.cycle(nodes)

        self.connected = False      #: public, is connected to broker?

        from .handler import ClusterHandlerThread
        self.thread = ClusterHandlerThread(self)

    def send(self, message, exchange=None, routing_key='', on_completed=None, on_failed=None):
        """
        Schedule a message to be sent.
        :param message: Message object to send
        :param exchange: Exchange to use. Leave None to use the default exchange
        :param routing_key: routing key to use
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        :return: a Future with this order's status
        """
        a = SendMessage(message, exchange or Exchange.direct, routing_key,
                        on_completed=on_completed, on_failed=on_failed)
        self.thread.order_queue.append(a)
        return a

    def declare_exchange(self, exchange, on_completed=None, on_failed=None):
        """
        Declare an exchange
        :param exchange: Exchange to declare
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        :return: a Future with this order's status
        """
        a = DeclareExchange(exchange, on_completed=on_completed, on_failed=on_failed)
        self.thread.order_queue.append(a)
        return a

    def declare_queue(self, queue, on_completed=None, on_failed=None):
        """
        Declares a queue
        :param queue: Queue to declare
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        :return: a Future with this order's status
        """
        a = DeclareQueue(queue, on_completed=on_completed, on_failed=on_failed)
        self.thread.order_queue.append(a)
        return a

    def delete_exchange(self, exchange, on_completed=None, on_failed=None):
        """
        Delete an exchange
        :param exchange: Exchange to delete
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        :return: a Future with this order's status
        """
        a = DeleteExchange(exchange, on_completed=on_completed, on_failed=on_failed)
        self.thread.order_queue.append(a)
        return a


    def delete_queue(self, queue, on_completed=None, on_failed=None):
        """
        Delete a queue
        :param queue: Queue to delete
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        :return: a Future with this order's status
        """
        a = DeleteQueue(queue, on_completed=on_completed, on_failed=on_failed)
        self.thread.order_queue.append(a)
        return a

    def cancel(self, queue, on_completed=None, on_failed=None):
        """
        Cancel consuming from a queue

        :param queue: Queue to consume from
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        :return: a Future with this order's status
        """
        a = CancelQueue(queue, on_completed=on_completed, on_failed=on_failed)
        self.thread.order_queue.append(a)
        return a

    def qos(self, prefetch_window, prefetch_count):
        a = SetQoS(prefetch_window, prefetch_count)
        self.thread.order_queue.append(a)
        return a

    def consume(self, queue, on_completed=None, on_failed=None):
        """
        Start consuming from a queue

        This queue will be declared to the broker. If this queue has any binds
        (.exchange field is not empty), queue will be binded to exchanges.

        :param queue: Queue to consume from
        :param on_completed: callable/0 to call when this succeeds
        :param on_failed: callable/1 to call when this fails with AMQPError instance
        :return: a Future with this order's status
        """
        a = ConsumeQueue(queue, on_completed=on_completed, on_failed=on_failed)
        self.thread.order_queue.append(a)
        return a

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
        try:
            if wait == 0:
                return self.thread.event_queue.get(False)
            else:
                return self.thread.event_queue.get(True, wait)
        except Queue.Empty:
            return None

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
