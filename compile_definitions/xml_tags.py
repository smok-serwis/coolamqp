# coding=UTF-8
from __future__ import print_function, absolute_import, division

import copy
import logging

import math

from compile_definitions.xml_fields import *
from coolamqp.framing.base import BASIC_TYPES, DYNAMIC_BASIC_TYPES

logger = logging.getLogger(__name__)


def _boolint(x):
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
        _SimpleField('value', int),
        _ValueField('class', 'kind', default=''),
        _docs,
    ]


class Field(BaseObject):
    NAME = 'field'
    FIELDS = [
        _name,
        _ValueField(('domain', 'type'), 'type', str),
        _SimpleField('label', default=None),
        _SimpleField('reserved', _boolint, default=0),
        _ComputedField('basic_type', lambda elem: elem.attrib.get('type',
                                                                  '') == elem.attrib.get(
            'name', '')),
        _docs
    ]


class Domain(BaseObject):
    NAME = 'domain'
    FIELDS = [
        _name,
        _SimpleField('type'),
        _ComputedField('elementary',
                       lambda a: a.attrib['type'] == a.attrib['name'])
    ]


class Method(BaseObject):
    NAME = 'method'
    FIELDS = [
        _name,
        _SimpleField('synchronous', _boolint, default=False),
        _SimpleField('index', int),
        _SimpleField('label', default=None),
        _docs,
        _ChildField('fields', 'field', Field),
        _ChildField('response', 'response', lambda e: e.attrib['name']),
        _ChildField('sent_by_client', 'chassis',
                    lambda e: e.attrib.get('name', '') == 'client',
                    postexec=any),
        _ChildField('sent_by_server', 'chassis',
                    lambda e: e.attrib.get('name', '') == 'server',
                    postexec=any),
        _ChildField('constant', 'field', lambda e: Field(e).reserved,
                    postexec=all)
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
        _SimpleField('index', int),
        _docs_with_label,
        _ChildField('methods', 'method', Method, postexec= \
            _cls_method_postexec),
        _ChildField('properties', 'field', Field)
    ]
