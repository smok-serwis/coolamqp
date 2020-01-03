# coding=UTF-8
"""
This is the layer that you talk to. It abstracts away one (in future - more) connections
to broker with an uniform interface.
"""
from __future__ import print_function, absolute_import, division

from coolamqp.clustering.cluster import Cluster
from coolamqp.clustering.events import MessageReceived, NothingMuch, \
    ConnectionLost

__all__ = ['Cluster', 'MessageReceived', 'NothingMuch', 'ConnectionLost']
