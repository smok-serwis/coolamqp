import itertools

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
            self._amqpargs = {
                'host': kwargs['host'],
                'userid': kwargs['user'],
                'password': kwargs['password'],
                'virtual_host': kwargs.get('vhost', '/'),
            }

    def __str__(self):
        return '%s@%s/%s' % (self._amqpargs['userid'],
                             self._amqpargs['host'],
                             self._amqpargs['virtual_host'])



class Cluster(object):
    """
    Represents connection to an AMQP cluster. This internally connects only to one node.
    """

    def __init__(self, nodes):
        """
        Construct the cluster definition
        :param nodes: iterable of nodes to try connecting, in this order.
            if list if exhaused, it will be started from beginning
        """

        self.node_to_connect_to = itertools.cycle(nodes)

    def start(self):
        """
        Connect to the cluster.
        :return: self
        """
        from .handler import ClusterHandlerThread
        self.thread = ClusterHandlerThread(self)
        self.thread.start()
        return self

    def shutdown(self):
        """
        Cleans everything and returns
        """
        self.thread.terminate()
        self.thread.join()
        return