import os
import logging

logger = logging.getLogger(__name__)


if 'ENABLE_GEVENT' in os.environ:
    import gevent.monkey
    logger.warning('Monkey patching the environment with gevent!')
    gevent.monkey.patch_all()
