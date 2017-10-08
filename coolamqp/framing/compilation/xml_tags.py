# coding=UTF-8
from __future__ import print_function, absolute_import, division
import six
import logging
import copy
import math
from coolamqp.framing.base import BASIC_TYPES, DYNAMIC_BASIC_TYPES
from .xml_fields import *

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
        _SimpleField('reserved', lambda x: bool(int(x)), default=0),
        _ComputedField('basic_type', lambda elem: elem.attrib.get('type', '') == elem.attrib.get('name', '')),
        _docs
    ]

class Class(BaseObject):
    NAME = 'class'
    FIELDS = [
        _name,
        _SimpleField('index', int),
        _docs_with_label,
        _ComputedField('methods', lambda elem: sorted(map(Method, _get_tagchild(elem, 'method')),
            key=lambda m: (m.name.strip('-')[0], -len(m.response)))),
        _ComputedField('properties', lambda elem: map(Field, _get_tagchild(elem, 'field')))
    ]


class Domain(BaseObject):
    NAME = 'domain'
    FIELDS = [
        _name,
        _SimpleField('type'),
        _ComputedField('elementary', lambda a: a.attrib['type'] == a.attrib['name'])
    ]


def _get_tagchild(elem, tag):
    return [e for e in elem.getchildren() if e.tag == tag]

class Method(BaseObject):
    NAME = 'method'
    FIELDS = [
        _name,
        _SimpleField('synchronous', _boolint, default=False),
        _SimpleField('index', int),
        _SimpleField('label', default=None),
        _docs,
        _ComputedField('fields', lambda elem: [Field(fie) for fie in _get_tagchild(elem, 'field')]),
        _ComputedField('response', lambda elem: [e.attrib['name'] for e in elem.findall('response')]),
        _ComputedField('sent_by_client', lambda elem:  any(e.attrib.get('name', '') == 'server' for e in
                           _get_tagchild(elem, 'chassis'))),
        _ComputedField('sent_by_server', lambda elem: any(e.attrib.get('name', '') == 'client' for e in
                           _get_tagchild(elem, 'chassis'))),
        _ComputedField('constant', lambda elem: all(Field(fie).reserved for fie in _get_tagchild(elem, 'field'))),
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
        for field in self.fields:
            if field.basic_type in DYNAMIC_BASIC_TYPES:
                return False
        return True
