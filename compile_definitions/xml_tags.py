# coding=UTF-8
from __future__ import print_function, absolute_import, division

import copy
import logging
import math

from compile_definitions.xml_fields import *
from coolamqp.framing.base import BASIC_TYPES, DYNAMIC_BASIC_TYPES

logger = logging.getLogger(__name__)


def bool_int(x):
    return bool(int(x))


__all__ = [
    'Domain', 'Method', 'Class', 'Field', 'Constant'
]


class BaseObject(object):
    FIELDS = []

    # tuples of (xml name, field name, type, (optional) default value)

    def __init__(self, elem):
        for ft in self.FIELDS:
            ft.set(self, elem)

    @classmethod
    def findall(cls, xml):
        return [cls(p) for p in xml.findall(cls.NAME)]

    def _replace(self, **kwargs):
        c = copy.copy(self)
        c.__dict__.update(**kwargs)
        return c


class Constant(BaseObject):
    NAME = 'constant'
    FIELDS = [
        _name,
        SimpleField('value', int),
        ValueField('class', 'kind', default=''),
        _docs,
    ]


class Field(BaseObject):
    NAME = 'field'
    FIELDS = [
        _name,
        ValueField(('domain', 'type'), 'type', str),
        SimpleField('label', default=None),
        SimpleField('reserved', bool_int, default=0),
        ComputedField('basic_type', lambda elem: elem.attrib.get('type',
                                                                  '') == elem.attrib.get(
            'name', '')),
        _docs
    ]


class Domain(BaseObject):
    NAME = 'domain'
    FIELDS = [
        _name,
        SimpleField('type'),
        ComputedField('elementary',
                      lambda a: a.attrib['type'] == a.attrib['name'])
    ]


class Method(BaseObject):
    NAME = 'method'
    FIELDS = [
        _name,
        SimpleField('synchronous', bool_int, default=False),
        SimpleField('index', int),
        SimpleField('label', default=None),
        _docs,
        ChildField('fields', 'field', Field),
        ChildField('response', 'response', lambda e: e.attrib['name']),
        ChildField('sent_by_client', 'chassis',
                   lambda e: e.attrib.get('name', '') == 'client',
                   post_exec=any),
        ChildField('sent_by_server', 'chassis',
                   lambda e: e.attrib.get('name', '') == 'server',
                   post_exec=any),
        ChildField('constant', 'field', lambda e: Field(e).reserved,
                   post_exec=all)
    ]

    def get_static_body(self):  # only arguments part
        body = []
        bits = 0
        for field in self.fields:

            if bits > 0 and field.basic_type != 'bit':
                body.append(b'\x00' * math.ceil(bits / 8))
                bits = 0

            if field.basic_type == 'bit':
                bits += 1
            else:
                body.append(eval(BASIC_TYPES[field.basic_type][2]))
        return b''.join(body)

    def is_static(self, domain_to_type=None):  # is size constant?
        return not any(
            field.basic_type in DYNAMIC_BASIC_TYPES for field in self.fields)


_cls_method_sortkey = lambda m: (m.name.strip('-')[0], -len(m.response))
_cls_method_postexec = lambda q: sorted(q, key=_cls_method_sortkey)


class Class(BaseObject):
    NAME = 'class'
    FIELDS = [
        _name,
        SimpleField('index', int),
        _docs_with_label,
        ChildField('methods', 'method', Method, post_exec= \
            _cls_method_postexec),
        ChildField('properties', 'field', Field)
    ]
