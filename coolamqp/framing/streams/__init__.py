# coding=UTF-8
"""
Classes that allow to receive and send frames in a rapid way
"""
from __future__ import absolute_import, division, print_function
import socket
import collections

from coolamqp.framing.streams.exceptions import StreamIsDead


