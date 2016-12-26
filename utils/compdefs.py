from xml.etree import ElementTree
import collections
import struct
import six

from getp import get_constants, get_classes, get_domains, byname, name_class, name_method, name_field, \
                 BASIC_TYPES

def frepr(p, sop=six.text_type):
    if isinstance(p, basestring):
        p = sop(p)
    s = repr(p)

    if isinstance(p, basestring) and not s.startswith('u'):
        return ('u' if sop == six.text_type else 'b') + s
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
    doc = [] if doc is None else [q.strip() for q in doc.split(u'\n') if len(q.strip()) > 0]
    pre = u' '*prefix

    doc = label + doc

    if len(doc) == 0:
        return u''

    doc[0] = doc[0].capitalize()

    if len(doc) == 1:
        return doc[0]

    doc = filter(lambda p: len(p.strip()) > 0, doc)

    if blank:
        doc = [doc[0], u''] + doc[1:]

    f = (u'\n'.join(pre + lin for lin in doc))[prefix:]
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
A Python version of the AMQP machine-readable specification.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See utils/compdefs.py for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016 DMS Serwis s.c.
"""

import struct

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
    FIELDS = []

    def write_arguments(self, out):
        """
        Write the argument portion of this frame into out.

        :param out: a callable that will be invoked (possibly many times) with
            parts of the arguments section.
        :type out: callable(part_of_frame: binary type) -> nevermind
        """

''')

        # Output classes
        for cls in get_classes(xml):
            line('''\nclass %s(AMQPClass):
    """
    %s
    """
    NAME = %s
    INDEX = %s

''', name_class(cls.name), doxify(None, cls.docs), frepr(cls.name), cls.index)

            for method in cls.methods:

                is_static = method.is_static(domain_to_basic_type)
                if is_static:
                    static_size = method.get_size(domain_to_basic_type)

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
    BINARY_HEADER = b'%s'
    IS_SIZE_STATIC = %s
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
                     u', '.join([name_class(cls.name)+name_method(kidname) for kidname in method.response]),
                     u''.join(map(lambda x: u'\\x'+(('0'+hex(x)[2:] if x < 16 else hex(x)[2:]).upper()),
                                        [cls.index, method.index])),
                     repr(is_static)
                     )

                # Static size
                if is_static:
                    line('    STATIC_ARGUMENT_SIZE = %s # length of arguments (as binary) is constant here\n', static_size)

                # Am I a response somewhere?
                for paren in cls.methods:
                    if method.name in paren.response:
                        line('    RESPONSE_TO = %s%s # this is sent in response to %s\n', name_class(cls.name), name_method(paren.name),
                             cls.name+'.'+paren.name
                             )

                # fields
                if len(method.fields) > 0:
                    line('    FIELDS = [ # tuples of (field name, field domain, basic type used, is_reserved)')

                    for field in method.fields:
                        tp = field.type
                        while tp in domain_to_basic_type:
                            tp = domain_to_basic_type[tp]

                        line('\n        (%s, %s, %s, %s), ', frepr(field.name), frepr(field.type), frepr(tp), repr(field.reserved))
                        if field.label:
                            line(' # '+field.label)

                    line('\n    ]\n')

                non_reserved_fields = [field for field in method.fields if not field.reserved]

                # constructor
                line('''\n    def __init__(%s):
        """
        Create frame %s
''',
                     u', '.join(['self'] + [name_field(field.name) for field in non_reserved_fields]),
                     cls.name + '.' + method.name,
                     )

                if len(non_reserved_fields) > 0:
                    line('\n')
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
                if len(method.fields) > 0:
                    line('''\n    def write_arguments(self, out):
        """
        Return this method frame as binary

        :param out: a callable that will be invoked (possibly many times) with
            parts of the arguments section.
        :type out: callable(part_of_frame: binary type) -> nevermind
        """
''')
                    def emit_structs(su):
                        if len(su) == 0:
                            return
                        line("        out(struct.pack('!")
                        line(''.join(a for a, b in su))
                        line("', ")
                        line(', '.join(b for a, b in su))
                        line('))\n')

                    good_structs = []
                    for field in method.fields:
                        if field.type not in BASIC_TYPES:
                            tp = domain_to_basic_type[field.type]
                        else:
                            tp = field.type

                        if BASIC_TYPES[tp][1] is None:
                            # struct can't do it

                            if tp == 'longstr':
                                good_structs.append(('L', 'len(self.'+name_field(field.name)+')'))

                            emit_structs(good_structs)
                            good_structs = []

                            # emit ours
                            if tp == 'longstr':
                                line('        out(self.'+name_field(field.name)+')\n')
                        else:
                            # special case - empty string
                            if tp == 'shortstr' and field.reserved:
                                continue    # just skip :)

                            val = 'self.'+name_field(field.name) if not field.reserved else frepr(BASIC_TYPES[tp][2], sop=six.binary_type)
                            good_structs.append((BASIC_TYPES[tp][1], val))
                    emit_structs(good_structs)
                    line('\n')



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
