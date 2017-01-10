# coding=UTF-8
from __future__ import absolute_import, division, print_function

import math
from collections import namedtuple

import six

from coolamqp.framing.base import BASIC_TYPES, DYNAMIC_BASIC_TYPES

# docs may be None



Constant = namedtuple('Constant', ('name', 'value', 'kind', 'docs'))  # kind is AMQP constant class # value is int
Field = namedtuple('Field', ('name', 'type', 'label', 'docs', 'reserved', 'basic_type')) # reserved is bool
Method = namedtuple('Method', ('name', 'synchronous', 'index', 'label', 'docs', 'fields', 'response',
                               'sent_by_client', 'sent_by_server', 'constant'))
        # synchronous is bool, constant is bool
        # repponse is a list of method.name
Class_ = namedtuple('Class_', ('name', 'index', 'docs', 'methods', 'properties'))   # label is int
Domain = namedtuple('Domain', ('name', 'type', 'elementary'))   # elementary is bool


class Method(object):
    def __init__(self, name, synchronous, index, label, docs, fields, response, sent_by_client, sent_by_server):
        self.name = name
        self.synchronous = synchronous
        self.index = index
        self.fields = fields
        self.response = response
        self.label = label
        self.docs = docs
        self.sent_by_client = sent_by_client
        self.sent_by_server = sent_by_server

        self.constant = len([f for f in self.fields if not f.reserved]) == 0

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

    def is_static(self, domain_to_type=None):    # is size constant?
        for field in self.fields:
            if field.basic_type in DYNAMIC_BASIC_TYPES:
                return False
        return True


def get_size(fields):   # assume all fields have static length
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
                size += len(BASIC_TYPES[field.basic_type][2])   # default minimum entry
        else:
            size += BASIC_TYPES[field.basic_type][0]

    if bits > 0:    # sync bits
        size += int(math.ceil(bits / 8))

    return size


def get_docs(elem):
    for kid in elem.getchildren():

        if kid.tag == 'rule':
            return get_docs(kid)

        s = kid.text.strip().split('\n')
        return u'\n'.join([u.strip() for u in s if len(u.strip()) > 0])

    return None


def for_domain(elem):
    a = elem.attrib
    return Domain(six.text_type(a['name']), a['type'], a['type'] == a['name'])


def for_field(elem): # for <field> in <method>
    a = elem.attrib
    return Field(six.text_type(a['name']), a['domain'] if 'domain' in a else a['type'],
                 a.get('label', None),
                 get_docs(elem),
                 a.get('reserved', '0') == '1',
                 None)

def for_method(elem):       # for <method>
    a = elem.attrib
    return Method(six.text_type(a['name']), bool(int(a.get('synchronous', '0'))), int(a['index']), a.get('label', None), get_docs(elem),
                  [for_field(fie) for fie in elem.getchildren() if fie.tag == 'field'],
                  [e.attrib['name'] for e in elem.findall('response')],
                  # if chassis=server that means server has to accept it
                  any([e.attrib.get('name', '') == 'server' for e in elem.getchildren() if e.tag == 'chassis']),
                  any([e.attrib.get('name', '') == 'client' for e in elem.getchildren() if e.tag == 'chassis'])
                  )

def for_class(elem):        # for <class>
    a = elem.attrib
    methods = sorted([for_method(me) for me in elem.getchildren() if me.tag == 'method'], key=lambda m: (m.name.strip('-')[0], -len(m.response)))
    return Class_(six.text_type(a['name']), int(a['index']), get_docs(elem) or a['label'], methods,
                  [for_field(e) for e in elem.getchildren() if e.tag == 'field'])

def for_constant(elem):     # for <constant>
    a = elem.attrib
    return Constant(a['name'], int(a['value']), a.get('class', ''), get_docs(elem))


def get_constants(xml):
    return [for_constant(e) for e in xml.findall('constant')]

def get_classes(xml):
    return [for_class(e) for e in xml.findall('class')]

def get_domains(xml):
    return [for_domain(e) for e in xml.findall('domain')]


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
        return methodname[0:i].capitalize() + methodname[i+1].upper() + methodname[i+2:]
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

    if isinstance(p, (six.binary_type, six.text_type)) and not s.startswith('u'):
        return ('u' if sop == six.text_type else 'b') + s
    else:
        return s

def to_code_binary(p):
    body = []
    for q in p:
        z = (hex(ord(q))[2:].upper())
        if len(z) == 1:
            z = u'0' + z
        body.append(u'\\x' + z)
    return u"b'"+(u''.join(body))+u"'"

def pythonify_name(p):
    return p.strip().replace('-', '_').upper()

def try_to_int(p):
    try:
        return int(p)
    except ValueError:
        return p

def to_docstring(label, doc, prefix=4, blank=True): # output a full docstring section
    label = [] if label is None else [label]
    doc = [] if doc is None else [q.strip() for q in doc.split(u'\n') if len(q.strip()) > 0]
    pre = u' '*prefix

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
