import logging
import multiprocessing
import os
import sys
import time

from coolamqp import __version__

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

if __name__ == '__main__':
    if sys.version.startswith('2.7'):
        logger.critical('This will not run on Python 2.x1')
        sys.exit(0)

    logger.warning('Starting stress tests on CoolAMQP v%s', __version__)

    from queue import Empty

    notify_client, result_client, notify_server, result_server = multiprocessing.Queue(), \
                                                                 multiprocessing.Queue(), \
                                                                 multiprocessing.Queue(), \
                                                                 multiprocessing.Queue()

    from .client import run as run_client
    from .server import run as run_server

    server = multiprocessing.Process(target=run_server, args=(
        notify_client, result_client, notify_server, result_server))
    client = multiprocessing.Process(target=run_client, args=(
        notify_client, result_client, notify_server, result_server))

    server.start()
    client.start()

    try:
        time.sleep(40)
    except KeyboardInterrupt:
        pass
    logger.warning('Finishing up')

    notify_client.put('term')
    notify_server.put('term')

    client.join(timeout=5.0)

    try:
        try:
            obj = result_server.get(timeout=1.0)
            if obj == 'fail':
                sys.exit(1)
        except Empty:
            pass

        try:
            obj = result_client.get(timeout=1.0)
            if obj == 'fail':
                sys.exit(1)
        except Empty:
            pass
    finally:
        try:
            if server.is_alive():
                os.kill(server.pid, 9)
        except OSError:
            pass

        try:
            if client.is_alive():
                os.kill(client.pid, 9)
        except OSError:
            pass
