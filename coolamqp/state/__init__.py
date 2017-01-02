# coding=UTF-8
from __future__ import absolute_import, division, print_function
"""
Any operations the user does, are against the BROKER STATE.

The connections are not important - what is important, is the broker state. This is a virtual
aggregate of all operations that are running against the cluster - ie. queues subscribed,
messages pending to be sent.

The client doesn't matter how this is handled. CoolAMQP (in the future) may decide to subscribe some
queues against other node, if it decides that the master queue is there, or do something entirely else.
"""