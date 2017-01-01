# coding=UTF-8
from __future__ import absolute_import, division, print_function
"""
You can feed Broker with some orders.
They work pretty much like futures.
"""
import threading


class BaseOrder(object):
    def __init__(self, on_completed=None, on_failed=None):
        self.lock = threading.Lock()
        self.lock.acquire()
        self.on_completed = on_completed
        self.on_failed = on_failed

    def on_done(self):
        if self.on_completed is not None:
            self.on_completed()
        self.lock.release()

    def on_fail(self):
        if self.on_failed is not None:
            self.on_failed()
        self.lock.release()

    def wait(self):
        self.lock.acquire()


class LinkSetup(BaseOrder):
    """
    Connecting to broker
    """

class ConsumeOnChannel(BaseOrder):
    """

    """