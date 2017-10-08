# coding=UTF-8
from __future__ import absolute_import, division, print_function

import math

import six

from coolamqp.framing.base import BASIC_TYPES, DYNAMIC_BASIC_TYPES

# docs may be None

class _Required(object):
    pass

class _Field(object):

    def set(self, obj, elem):
        obj.__dict__[self.field_name] = self.find(elem)

    def __init__(self, field_name):
        self.field_name = field_name

    def find(self, elem):
        raise NotImplementedError('abstract')


class _ComputedField(_Field):
    def __init__(self, field_name, find_fun):
        super(_ComputedField, self).__init__(field_name)
        self.find = find_fun


class _ValueField(_Field):
    def __init__(self, xml_names, field_name, field_type=lambda x: x,
                 default=_Required):
        self.xml_names = (xml_names,) if isinstance(xml_names,
                                                    six.text_type) else xml_names
        self.field_name = field_name
        self.field_type = field_type
        self.default = default

    def find(self, elem):
        return self.field_type(self._find(elem))

    def _find(self, elem):
        for xmln in self.xml_names:
            if xmln in elem.attrib:
                return elem.attrib[xmln]
        else:
            if self.default is _Required:
                raise TypeError('Expected field')
            else:
                return self.default


class _SimpleField(_ValueField):
    def __init__(self, name, field_type=None, default=_Required):
        super(_SimpleField, self).__init__(name, name, field_type, default=default)


def get_docs(elem, label=False):
    """Parse an XML element. Return documentation"""
    for kid in elem.getchildren():

        if kid.tag == 'rule':
            return get_docs(kid)

        s = kid.text.strip().split('\n')
        return u'\n'.join([u.strip() for u in s if len(u.strip()) > 0])

    if label:
        return elem.attrib.get('label', None)

_name = _SimpleField('name', unicode)
_docs = _ComputedField('docs', lambda elem: get_docs(elem))

class BaseObject(object):

    FIELDS = []
    # tuples of (xml name, field name, type, (optional) default value)

    def __init__(self, *args):

        if len(args) == 1:
            elem, = args

            self.docs = get_docs(elem)

            for ft in (_Field(*args) for args in self.FIELDS):
                ft.set(self, elem)
        else:
            for fname, value in zip(['name'] + [k[1] for k in self.FIELDS] + ['docs']):
                self.__dict__[fname] = value

    @classmethod
    def findall(cls, xml):
        return [cls(p) for p in xml.findall(cls.NAME)]


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
        _SimpleField('label', None),
        _SimpleField('reserved', lambda x: bool(int(x)), default=0),
        _ComputedField('basic_type', lambda elem: elem.attrib['type'] == elem.attrib['name']),
        _docs
    ]

class Class(BaseObject):
    NAME = 'class'
    FIELDS = [
        _name,
        _ValueField('index', int),
        _ComputedField('docs', lambda elem: get_docs(elem, label=True)),
        _ComputedField('methods', lambda elem: sorted(
            [Method(me) for me in elem.getchildren() if me.tag == 'method'],
            key=lambda m: (m.name.strip('-')[0], -len(m.response)))),
        _ComputedField('properties', lambda elem: [Field(e) for e in elem.getchildren() if
                   e.tag == 'field'])
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



_boolint = lambda x: bool(int(x))

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
    return data
