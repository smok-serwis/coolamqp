# coding=UTF-8
"""
Classes that allow to receive and send frames
REASONABLY FAST, because they use buffers and stuff.
"""
from __future__ import absolute_import, division, print_function

from coolamqp.uplink.streams.recv_formatter import ReceivingFormatter
from coolamqp.uplink.streams.send_operator import SendingOperator
