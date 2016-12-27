# coding=UTF-8
"""
Set of objects and functions whose job is to construct an Uplink
instance capable of further action and bootstrap.
"""
from __future__ import absolute_import, division, print_function

from coolamqp.uplink.frames.base import AMQP_HELLO_HEADER

import socket


def connect(host, port, connect_timeout=10,
                        general_timeout=5):
    """
    Return a TCP socket connected to broker.

    Socket should be in the state of 'Awaiting Connection.Start'

    This may block for up to connect_timeout seconds.

    When returned, this socket will be in the state of awaiting
    an

    :param host: host to connect to
    :type host: text
    :param port: port to connect to
    :type port: int
    :return: a CONNECTED socket or None, if connection failed.
    """

    try:
        s = socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(connect_timeout)
        s.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)
        s.connect((host, port))
        s.send(AMQP_HELLO_HEADER)
        s.settimeout(0)
    except (IOError, socket.error, socket.timeout):
        try:
            s.close()
        except:
            pass
        return None
