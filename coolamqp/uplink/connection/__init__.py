# coding=UTF-8
"""
Comprehensive management of a framing connection.

Connection is something that can:
 - call something when an AMQPFrame is received
 - send AMQPFrame's
"""
from __future__ import absolute_import, division, print_function

from coolamqp.uplink.connection.connection import Connection
