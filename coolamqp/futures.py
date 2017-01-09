# coding=UTF-8
from __future__ import absolute_import, division, print_function
import concurrent.futures
import threading
import logging


logger = logging.getLogger(__name__)


class Future(concurrent.futures.Future):
    """
    A strange future (only one thread may wait for it)
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.lock.acquire()

        self.completed = False
        self.successfully = None
        self._result = None
        self.cancelled = False
        self.running = True

        self.callables = []

    def add_done_callback(self, fn):
        self.callables.append(fn)

    def result(self, timeout=None):
        assert timeout is None, u'Non-none timeouts not supported'
        self.lock.acquire()

        if self.completed:
            if self.successfully:
                return self._result
            else:
                raise self._result
        else:
            if self.cancelled:
                raise concurrent.futures.CancelledError()
            else:
                # it's invalid to release the lock, not do the future if it's not cancelled
                raise RuntimeError(u'Invalid state!')

    def cancel(self):
        """
        When cancelled, future will attempt not to complete (completed=False).
        :return:
        """
        self.cancelled = True

    def __finish(self, result, successful):
        self.completed = True
        self.successfully = successful
        self._result = result
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
