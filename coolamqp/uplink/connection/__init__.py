# coding=UTF-8
"""
Comprehensive management of a framing connection.

Connection is something that can:
 - call something when an AMQPFrame is received
 - send AMQPFrame's

 Pretty much CoolAMQP is about persistent "attaches" that attach to transient connection
 (they die when down) to do stuff, ie. send messages, consume, etc.
"""
from __future__ import absolute_import, division, print_function

from coolamqp.uplink.connection.connection import Connection
from coolamqp.uplink.connection.watches import FailWatch, Watch, \
    HeaderOrBodyWatch, MethodWatch, AnyWatch
from coolamqp.uplink.connection.states import ST_OFFLINE, ST_CONNECTING, \
    ST_ONLINE
