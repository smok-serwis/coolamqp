# coding=UTF-8
from __future__ import absolute_import, division, print_function



class NodeDefinition(object):
    """
    Definition of a node
    """

    def __init__(self, host, port, user, password, virtual_host='/', heartbeat=None):
        """
        All necessary information to establish a link to a broker.

        :param host: TCP host, str
        :param port: TCP port, int
        :param user: AMQP user
        :param password: AMQP password
        :param virtual_host: AMQP virtual host
        :param amqp_version: AMQP protocol version
        """
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.heartbeat = heartbeat

