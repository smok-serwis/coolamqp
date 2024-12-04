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

    args = []
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            key = tobytes(key)
            args.append((key, (value, get_type_for(value))))
        return args, 'F'
    elif len(arguments[0]) == 2:
        for key, value in arguments:
            key = tobytes(key)
            args.append((key, (value, get_type_for(value))))
        return args, 'F'
    elif isinstance(arguments, (list, tuple)):
        for value in arguments:
            args.append((value, get_type_for(value)))
        return args, 'A'
    return args
