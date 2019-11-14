from __future__ import print_function
import os
import logging
import platform
import sys
logger = logging.getLogger(__name__)

print(os.environ, file=sys.stderr)
if 'ENABLE_GEVENT' in os.environ:
    if platform == 'PyPy':
        # gevent is not supported on PyPy
        sys.exit(0)
    import gevent.monkey
    print('Monkey patching the environment with gevent!', file=sys.stderr)
    gevent.monkey.patch_all()
