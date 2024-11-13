import warnings

import six

from coolamqp.framing.field_table import get_type_for
import logging

logger = logging.getLogger(__name__)



def tobytes(q):
    if isinstance(q, memoryview):
        return q.tobytes()
    return q.encode('utf-8') if isinstance(q, six.text_type) else q


def toutf8(q):
    if isinstance(q, memoryview):
        q = q.tobytes()
    return q.decode('utf-8') if isinstance(q, six.binary_type) else q


def argumentify(arguments):
    if arguments is None:
        return []
    logger.warning('Input is %s' % (arguments, ))
    # Was it argumented already?
    # if isinstance(arguments, list):
    #     if len(arguments) >= 1:
    #         if isinstance(arguments[0], tuple):
    #             if isinstance(arguments[0][1], str) and len(arguments[0][1]) == 1:
    #                 # Looks argumentified already
    #                 return arguments
    args = []
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            key = tobytes(key)
            args.append((key, (value, get_type_for(value))))
        logger.warning('Output is %s', (args, 'F'))
        return (args, 'F')
    elif len(arguments[0]) == 2:
        for key, value in arguments:
            key = tobytes(key)
            args.append((key, (value, get_type_for(value))))
            return (args, 'F')
    elif isinstance(arguments, (list, tuple)):
        for value in arguments:
            args.append((value, get_type_for(value)))
            return (args, 'A')
    else:
        warnings.warn('Unnecessary call to argumentify, see issue #11 for details', UserWarning)
        return args
