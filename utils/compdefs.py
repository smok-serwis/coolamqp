from xml.etree import ElementTree
import collections
import struct
import six

from getp import get_constants, get_classes, get_domains, byname, name_class, name_method, name_field

def frepr(p):
    if isinstance(p, basestring):
        p = six.text_type(p)
    s = repr(p)

    if isinstance(p, basestring) and not s.startswith('u'):
        return 'u' + s
    else:
        return s

def normname(p):
    return p.strip().replace('-', '_').upper()

def infertype(p):
    try:
        return int(p)
    except ValueError:
        return p

def doxify(label, doc, prefix=4, blank=True): # output a full docstring section
    label = [] if label is None else [label]
    doc = [] if doc is None else doc.split(u'\n')
    pre = u' '*prefix

    doc = label + doc

    if len(doc) == 0:
        return u'\n'

    doc[0] = doc[0].capitalize()

    if len(doc) == 1:
        return pre + doc[0] + u'\n'

    if blank:
        doc = [doc[0], u''] + doc[1:]

    f = (u'\n'.join(pre + lin for lin in doc))[prefix:]
    print(repr(f))
    return f

def ffmt(data, *args, **kwargs):
    for arg in args:
        op = str if kwargs.get('sane', True) else frepr
        data = data.replace('%s', op(arg), 1)
    return data

def compile_definitions(xml_file='resources/amqp0-9-1.xml', out_file='coolamqp/framing/definitions.py'):
    """parse resources/amqp-0-9-1.xml into """

    xml = ElementTree.parse(xml_file)

    with open(out_file, 'wb') as out:

        out.write('''# coding=UTF-8
from __future__ import print_function, absolute_import
"""
Constants used in AMQP protocol.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See utils/compdefs.py for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016 DMS Serwis s.c.
"""

''')

        def line(data, *args, **kwargs):
            out.write(ffmt(data, *args, sane=True))

        # Output core ones
        line('# Core frame types\n')
        for constant in get_constants(xml):
            g = ffmt('%s = %s', constant.name.strip().replace('-', '_').upper(), constant.value)
            line(g)
            if constant.docs:
                lines = constant.docs.split('\n')
                line(' # %s\n', lines[0])
                if len(lines) > 1:
                    for ln in lines[1:]:
                        line(u' '*len(g))
                        line(u' # %s\n', ln)
            else:
                line('\n')

        # get domains
        domain_to_basic_type = {}
        line('DOMAIN_TO_BASIC_TYPE = {\n')
        for domain in get_domains(xml):
            line(u'    %s: %s,\n', frepr(domain.name), frepr(None if domain.elementary else domain.type))
            if not domain.elementary:
                domain_to_basic_type[domain.name] = domain.type

        line('}\n')

        line('''

class AMQPClass(object):
    pass


class AMQPMethod(object):
    RESPONSE_TO = None
    REPLY_WITH = []


''')

        # Output classes
        for cls in get_classes(xml):
            line('''class %s(AMQPClass):
    """
    %s
    """
    NAME = %s
    INDEX = %s

''', name_class(cls.name), doxify(None, cls.docs), frepr(cls.name), cls.index)

            for method in cls.methods:


                line('''\nclass %s%s(AMQPMethod):
    """
    %s
    """
    CLASS = %s
    NAME = %s
    CLASSNAME = %s
    CLASS_INDEX = %s
    METHOD_INDEX = %s
    FULLNAME = %s
    SYNCHRONOUS = %s
    REPLY_WITH = [%s]
''',
                     name_class(cls.name), name_method(method.name),
                     doxify(method.label, method.docs),
                     name_class(cls.name),
                     frepr(method.name),
                     frepr(cls.name),
                     frepr(cls.index),
                     frepr(method.index),
                     frepr(cls.name + '.' + method.name),
                     repr(method.synchronous),
                     str(', '.join([name_class(cls.name)+name_method(kidname) for kidname in method.response])),
                     )

                # Am I a response somewhere?
                for paren in cls.methods:
                    if method.name in paren.response:
                        line('    RESPONSE_TO = %s%s\n', name_class(cls.name), name_method(paren.name))

                # fields
                line('    FIELDS = [')
                for field in method.fields:
                    tp = field.type
                    while tp in domain_to_basic_type:
                        tp = domain_to_basic_type[tp]

                    line('\n        (%s, %s, %s), ', frepr(field.name), frepr(field.type), frepr(tp))
                    if field.label:
                        line(' # '+field.label)

                line('\n    ]\n\n')

                non_reserved_fields = [field for field in method.fields if not field.reserved]

                # constructor
                line('''    def __init__(%s):
        """
        Create frame %s

''',
                     u', '.join(['self'] + [name_field(field.name) for field in non_reserved_fields]),
                     cls.name + '.' + method.name,
                     )

                for field in non_reserved_fields:
                    tp = field.type
                    while tp in domain_to_basic_type:
                        tp = domain_to_basic_type[tp]

                    if (field.label is not None) or (field.docs is not None):
                        line('        :param %s: %s\n', name_field(field.name),
                             doxify(field.label, field.docs, prefix=12, blank=False))
                    line('        :type %s: %s (as %s)\n', name_field(field.name), field.type, tp)

                line('        """\n')

                for field in non_reserved_fields:
                    line('        self.%s = %s\n', name_field(field.name), name_field(field.name))

                # end
                line('''\n    def to_frame(self):
        """
        Return self as bytes

        :return: AMQP frame payload
        """
        raise NotImplementedError()

''')



            # Get me a dict - (classid, methodid) => class of method
            dct = {}
            for cls in get_classes(xml):
                for method in cls.methods:
                    dct[((cls.index, method.index))] = '%s%s' % (name_class(cls.name), name_method(method.name))

        line('\nIDENT_TO_METHOD = {\n')
        for k, v in dct.items():
            line('    %s: %s,\n', repr(k), v)
        line('}\n\n')



if __name__ == '__main__':
    compile_definitions()
