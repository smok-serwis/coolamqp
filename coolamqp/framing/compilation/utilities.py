# coding=UTF-8
from __future__ import absolute_import, division, print_function

import math

import six

from coolamqp.framing.base import BASIC_TYPES

from .xml_tags import *


# docs may be None




def get_size(fields):  # assume all fields have static length
    """Assuming all fields have static length, return their length together. Supports bits"""
    size = 0
    bits = 0
    for field in fields:

        if (bits > 0) and (field.basic_type != 'bit'):  # sync bits
            size += int(math.ceil(bits / 8))
            bits = 0

        if BASIC_TYPES[field.basic_type][0] is None:
            if field.basic_type == 'bit':
                bits += 1
            else:
                size += len(
                    BASIC_TYPES[field.basic_type][2])  # default minimum entry
        else:
            size += BASIC_TYPES[field.basic_type][0]

    if bits > 0:  # sync bits
        size += int(math.ceil(bits / 8))

    return size


def as_unicode(callable):
    def roll(*args, **kwargs):
        return six.text_type(callable(*args, **kwargs))

    return roll


def to_dict_by_name(list_of_things):
    return dict((a.name, a) for a in list_of_things)


@as_unicode
def name_class(classname):
    """Change AMQP class name to Python class name"""
    return classname.capitalize()


@as_unicode
def format_method_class_name(methodname):
    if '-' in methodname:
        i = methodname.find('-')
        return methodname[0:i].capitalize() + methodname[
            i + 1].upper() + methodname[i + 2:]
    else:
        return methodname.capitalize()


@as_unicode
def format_field_name(field):
    if field in (u'global', u'type'):
        field = field + '_'
    return field.replace('-', '_')


def frepr(p, sop=six.text_type):
    if isinstance(p, (six.binary_type, six.text_type)):
        p = sop(p)
    s = repr(p)

    if isinstance(p, (six.binary_type, six.text_type)) and not s.startswith(
            'u'):
        return ('u' if sop == six.text_type else 'b') + s
    else:
        return s


def to_code_binary(p):
    body = []
    for q in p:
        if isinstance(q, int):
            q = six.int2byte(q)
        z = (hex(ord(q))[2:].upper())
        if len(z) == 1:
            z = u'0' + z
        body.append(u'\\x' + z)
    return u"b'" + (u''.join(body)) + u"'"


def pythonify_name(p):
    return p.strip().replace('-', '_').upper()


def try_to_int(p):
    try:
        return int(p)
    except ValueError:
        return p


def to_docstring(label, doc, prefix=4,
                 blank=True):  # output a full docstring section
    label = [] if label is None else [label]
    doc = [] if doc is None else [q.strip() for q in doc.split(u'\n') if
                                  len(q.strip()) > 0]
    pre = u' ' * prefix

    doc = label + doc

    if len(doc) == 0:
        return u''

    doc[0] = doc[0].capitalize()

    if len(doc) == 1:
        return doc[0]

    doc = [p for p in doc if len(p.strip()) > 0]

    if blank:
        doc = [doc[0], u''] + doc[1:]

    f = (u'\n'.join(pre + lin for lin in doc))[prefix:]
    return f


def ffmt(data, *args, **kwargs):
    for arg in args:
        op = str if kwargs.get('sane', True) else frepr
        data = data.replace('%s', op(arg), 1)
    data = data.replace('%S', '%s')
    return data
