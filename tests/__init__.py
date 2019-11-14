import os
import logging
import platform
import sys
logger = logging.getLogger(__name__)


if 'ENABLE_GEVENT' in os.environ:
    if platform == 'PyPy':
        # gevent is not supported on PyPy
        sys.exit(0)
    import gevent.monkey
    logger.warning('Monkey patching the environment with gevent!')
    gevent.monkey.patch_all()
