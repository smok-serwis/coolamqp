# coding=UTF-8
from __future__ import absolute_import, division, print_function
from collections import namedtuple
import six

# docs may be None

Constant = namedtuple('Constant', ('name', 'value', 'kind', 'docs'))  # kind is AMQP constant class # value is int
Field = namedtuple('Field', ('name', 'type', 'label', 'docs', 'reserved')) # reserved is bool
Method = namedtuple('Method', ('name', 'synchronous', 'index', 'label', 'docs', 'fields', 'response'))
        # synchronous is bool
        # repponse is a list of method.name
Class_ = namedtuple('Class_', ('name', 'index', 'docs', 'methods'))   # label is int
Domain = namedtuple('Domain', ('name', 'type', 'elementary'))   # elementary is bool

            # name => (length|None, struct ID|None, reserved-field-value : for struct if structable, bytes else)
BASIC_TYPES = {'bit': (1, '?', 0),
               'octet': (1, 'B', 0),
               'short': (2, 'H', 0),
               'long': (4, 'I', 0),
               'longlong': (8, 'L', 0),
               'timestamp': (8, 'L', 0),
               'table': (None, None, b'\x00\x00\x00\x00'),
               'longstr': (None, None, b'\x00\x00\x00\x00'),
               'shortstr': (None, 'p', '')
               }


class Method(object):
    def __init__(self, name, synchronous, index, label, docs, fields, response):
        self.name = name
        self.synchronous = synchronous
        self.index = index
        self.fields = fields
        self.response = response
        self.label = label
        self.docs = docs

    def get_size(self, domain_to_type): # for static methods
        size = 0
        for field in self.fields:
            tp = field.type
            while tp in domain_to_type:
                tp = domain_to_type[tp]
            if BASIC_TYPES[tp] is None:
                raise TypeError()
            size += BASIC_TYPES[tp]
        return size

    def is_static(self, domain_to_type):    # is size constant?
        try:
            self.get_size(domain_to_type)
        except TypeError:
            return False
        return True



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


def for_method_field(elem): # for <field> in <method>
    a = elem.attrib
    return Field(six.text_type(a['name']), a['domain'] if 'domain' in a else a['type'],
                 a.get('label', None),
                 get_docs(elem),
                 a.get('reserved', '0') == '1')


def for_method(elem):       # for <method>
    a = elem.attrib
    return Method(six.text_type(a['name']), bool(int(a.get('synchronous', '0'))), int(a['index']), a['label'], get_docs(elem),
                  [for_method_field(fie) for fie in elem.getchildren() if fie.tag == 'field'],
                  [e.attrib['name'] for e in elem.findall('response')]
                  )

def for_class(elem):        # for <class>
    a = elem.attrib
    methods = sorted([for_method(me) for me in elem.getchildren() if me.tag == 'method'], key=lambda m: (m.name.strip('-')[0], -len(m.response)))
    return Class_(six.text_type(a['name']), int(a['index']), get_docs(elem) or a['label'], methods)

def for_constant(elem):     # for <constant>
    a = elem.attrib
    return Constant(a['name'], int(a['value']), a.get('class', ''), get_docs(elem))


def get_constants(xml):
    return [for_constant(e) for e in xml.findall('constant')]

def get_classes(xml):
    return [for_class(e) for e in xml.findall('class')]

def get_domains(xml):
    return [for_domain(e) for e in xml.findall('domain')]


def a_text(callable):
    def roll(*args, **kwargs):
        return six.text_type(callable(*args, **kwargs))
    return roll

def byname(list_of_things):
    return dict((a.name, a) for a in list_of_things)

@a_text
def name_class(classname):
    """Change AMQP class name to Python class name"""
    return classname.capitalize()

@a_text
def name_method(methodname):
    if '-' in methodname:
        i = methodname.find('-')
        return methodname[0:i].capitalize() + methodname[i+1].upper() + methodname[i+2:]
    else:
        return methodname.capitalize()

@a_text
def name_field(field):
    if field in ('global', ):
        field = field + '_'
    return field.replace('-', '_')
