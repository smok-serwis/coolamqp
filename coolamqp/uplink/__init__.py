# coding=UTF-8
"""
The layer that allows you to attach Reactors,
ie. objects that are informed upon receiving a frame or connection dying.
They can also send frames themselves.
"""
from __future__ import absolute_import, division, print_function

from coolamqp.uplink.connection import Connection
from coolamqp.uplink.listener import ListenerThread
