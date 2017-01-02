# coding=UTF-8
from __future__ import absolute_import, division, print_function
import concurrent.futures
import threading
import logging


logger = logging.getLogger(__name__)


class BaseOrder(concurrent.futures.Future):
    """
    A strange future - only one thread may .wait() for it.
    And it's for the best.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.lock.acquire()

        self.completed = False
        self.successfully = None
        self.result = None
        self.cancelled = False
        self.running = True

        self.callables = []

    def add_done_callback(self, fn):
        self.callables.append(fn)

    def cancel(self):
        self.cancelled = True

    def __finish(self, result, successful):
        self.completed = True
        self.successfully = successful
        self.result = result
        self.lock.release()

        for callable in self.callables:
            try:
                callable(self)
            except Exception as e:
                logger.error('Exception in base order future: %s', repr(e))
            except BaseException as e:
                logger.critical('WILD NASAL DEMON APPEARED: %s', repr(e))

    def set_result(self, result=None):
        self.__finish(result, True)

    def set_exception(self, exception):
        self.__finish(exception, False)


class SendMessage(BaseOrder):
    """
    An order to send a message somewhere, such that message will survive disconnects
    from broker and so on.
    """
    def __init__(self, message, exchange_name, routing_key):
        """
        :param message: Message object to send
        :param exchange_name: bytes, name of exchange
        :param routing_key: bytes, routing key
        """
        BaseOrder.__init__(self)

        self.message = message
        self.exchange_name = exchange_name
        self.routing_key = routing_key

