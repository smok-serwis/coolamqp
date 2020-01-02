import logging
import multiprocessing
import sys
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    if sys.version.startswith('2.7'):
        logger.critical('This will not run on Python 2.x1')
        sys.exit(0)

    from queue import Empty

    notify_client, result_client, notify_server, result_server = multiprocessing.Queue(), multiprocessing.Queue(), multiprocessing.Queue(), multiprocessing.Queue()

    from .client import run as run_client
    from .server import run as run_server

    server = multiprocessing.Process(target=run_server, args=(
    notify_client, result_client, notify_server, result_server))
    client = multiprocessing.Process(target=run_client, args=(
    notify_client, result_client, notify_server, result_server))

    server.start()
    client.start()

    try:
        time.sleep(20)
    except KeyboardInterrupt:
        pass

    notify_client.put(None)
    notify_server.put(None)

    server.join()
    client.join()

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
