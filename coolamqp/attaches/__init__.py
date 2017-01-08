# coding=UTF-8
from __future__ import absolute_import, division, print_function
"""
Attaches are components that attach to an coolamqp.uplink.Connection and perform some duties
These duties almost require allocating a channel. The attache becomes then responsible for closing this channel.

Attache should also register at least one on_fail watch, so it can handle things if they go south.
"""

from coolamqp.attaches.consumer import Consumer
from coolamqp.attaches.publisher import Publisher, MODE_NOACK, MODE_CNPUB
