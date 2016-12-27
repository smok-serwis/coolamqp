# coding=UTF-8
"""
Classes that allow to receive and send frames in a rapid way,
and manage low-level connection details.

These modules bear no notion of fault-tolerance.
"""
from __future__ import absolute_import, division, print_function

from coolamqp.framing.streams.recv_formatter import ReceivingFormatter


