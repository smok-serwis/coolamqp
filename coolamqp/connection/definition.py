# coding=UTF-8
from __future__ import absolute_import, division, print_function
import six


class NodeDefinition(object):
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
            port - TCP port to use. Default is 5672
        """

        self.heartbeat = kwargs.pop('heartbeat', None)
        self.port = kwargs.pop('port', 5672)

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
        return six.text_type(b'amqp://%s:%s@%s/%s'.encode('utf8') % (self.host, self.port, self.user, self.virtual_host))
