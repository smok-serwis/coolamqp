# coding=UTF-8
"""

Core object here is Connection. This package:
    - establishes basic connectivity (up to the point where you can open channels yourself)
    - takes care of heartbeats

You can wait for a particular frame by setting watches on connections.
Watches will fire upon an event triggering them.

EVERYTHING HERE IS CALLED BY LISTENER THREAD UNLESS STATED OTHERWISE.

"""
from __future__ import absolute_import, division, print_function

from coolamqp.uplink.connection import Connection, HeaderOrBodyWatch, \
    MethodWatch, AnyWatch, FailWatch
from coolamqp.uplink.handshake import PUBLISHER_CONFIRMS, \
    CONSUMER_CANCEL_NOTIFY
from coolamqp.uplink.listener import ListenerThread
