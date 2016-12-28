from __future__ import division

import collections
import math
import struct
from xml.etree import ElementTree

import six
from coolamqp.framing.base import BASIC_TYPES

from coolamqp.framing.compilation.utilities import get_constants, get_classes, get_domains, \
    name_class, format_method_class_name, format_field_name, ffmt, to_docstring, pythonify_name, to_code_binary, \
    frepr, get_size

TYPE_TRANSLATOR = {
        'shortstr': 'binary type (max length 255)',
        'longstr': 'binary type',
        'table': 'table. See coolamqp.uplink.framing.field_table',
        'bit': 'bool',
        'octet': 'int, 8 bit unsigned',
        'short': 'int, 16 bit unsigned',
        'long': 'int, 32 bit unsigned',
        'longlong': 'int, 64 bit unsigned',
        'timestamp': '64 bit signed POSIX timestamp (in seconds)',
}

def compile_definitions(xml_file='resources/amqp0-9-1.xml', out_file='coolamqp/framing/definitions.py'):
    """parse resources/amqp-0-9-1.xml into """

    xml = ElementTree.parse(xml_file)
    out = open(out_file, 'wb')

    out.write('''# coding=UTF-8
from __future__ import print_function, absolute_import
"""
A Python version of the AMQP machine-readable specification.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See coolamqp.uplink.framing.compilation for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016 DMS Serwis s.c.
"""

import struct
import collections

from coolamqp.framing.base_definitions import AMQPClass, AMQPMethodPayload, AMQPContentPropertyList
from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size

Field = collections.namedtuple('Field', ('name', 'type', 'reserved'))

''')

    def line(data, *args, **kwargs):
        out.write(ffmt(data, *args, sane=True))

    # Output core ones
    FRAME_END = None
    con_classes = collections.defaultdict(list)
    line('# Core constants\n')
    for constant in get_constants(xml):
        if pythonify_name(constant.name) == 'FRAME_END':
            FRAME_END = constant.value
        g = ffmt('%s = %s', pythonify_name(constant.name), constant.value)
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

        if constant.kind:
            con_classes[constant.kind].append(pythonify_name(constant.name))

    for constant_kind, constants in con_classes.items():
        line('\n%s = [%s]', pythonify_name(constant_kind), u', '.join(constants))

    # get domains
    domain_to_basic_type = {}
    line('\n\n\nDOMAIN_TO_BASIC_TYPE = {\n')
    for domain in get_domains(xml):
        line(u'    %s: %s,\n', frepr(domain.name), frepr(None if domain.elementary else domain.type))
        domain_to_basic_type[domain.name] = domain.type

    line('}\n')

    class_id_to_contentpropertylist = {}

    # Output classes
    for cls in get_classes(xml):

        cls = cls._replace(properties=[p._replace(basic_type=domain_to_basic_type[p.type]) for p in cls.properties])

        line('''\nclass %s(AMQPClass):
    """
    %s
    """
    NAME = %s
    INDEX = %s

''',
             name_class(cls.name), to_docstring(None, cls.docs), frepr(cls.name), cls.index)

        if len(cls.properties) > 0:
            class_id_to_contentpropertylist[cls.index] = name_class(cls.name)+'ContentPropertyList'

            line('''\nclass %sContentPropertyList(AMQPContentPropertyList):
    """
    %s
    """
    FIELDS = [
''',

                 name_class(cls.name), to_docstring(None, cls.docs), frepr(cls.name), cls.index, name_class(cls.name))

            is_static = all(property.basic_type not in ('table', 'longstr', 'shortstr') for property in cls.properties)

            for property in cls.properties:
                line('        Field(%s, %s, %s),\n', frepr(property.name), frepr(property.basic_type), repr(property.reserved))
            line('    ]\n\n')







        # ============================================ Do methods for this class
        for method in cls.methods:
            full_class_name = '%s%s' % (name_class(cls.name), format_method_class_name(method.name))

            # annotate types
            method.fields = [field._replace(basic_type=domain_to_basic_type[field.type]) for field in method.fields]

            is_static = method.is_static()
            if is_static:
                static_size = get_size(method.fields)

            is_content_static = len([f for f in method.fields if not f.reserved]) == 0

            line('''\nclass %s(AMQPMethodPayload):
    """
    %s
    """
    NAME = %s

    INDEX = (%s, %s)          # (Class ID, Method ID)
    BINARY_HEADER = %s      # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = %s, %s
    REPLY_WITH = [%s]       # methods you can reply with to this one

    IS_SIZE_STATIC = %s     # this means that argument part has always the same length
    IS_CONTENT_STATIC = %s  # this means that argument part has always the same content
''',
                 full_class_name,
                 to_docstring(method.label, method.docs),
                 frepr(cls.name + '.' + method.name),
                 frepr(cls.index), frepr(method.index),
                 to_code_binary(chr(cls.index)+chr(method.index)),
                 repr(method.sent_by_client),
                 repr(method.sent_by_server),
                 u', '.join([name_class(cls.name) + format_method_class_name(kidname) for kidname in method.response]),
                 repr(is_static),
                 repr(is_content_static)
                 )


            if is_content_static:

                line('''    STATIC_CONTENT = %s  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END
''',
                     to_code_binary(struct.pack('!LBB', static_size + 4, cls.index, method.index) + \
                                    method.get_static_body() + \
                                    struct.pack('!B', FRAME_END)))

            # Am I a response somewhere?
            for paren in cls.methods:
                if method.name in paren.response:
                    line('    RESPONSE_TO = %s%s # this is sent in response to %s\n', name_class(cls.name), format_method_class_name(paren.name),
                         cls.name +'.' + paren.name
                         )

            # fields
            if len(method.fields) > 0:
                line('\n    # See constructor pydoc for details\n')
                line('    FIELDS = [ \n')

                for field in method.fields:
                    line('        Field(%s, %s, reserved=%s),\n', frepr(field.name), frepr(field.basic_type), repr(field.reserved))

                line('    ]\n')

            non_reserved_fields = [field for field in method.fields if not field.reserved]

            # constructor
            line('''\n    def __init__(%s):
        """
        Create frame %s
''',
                 u', '.join(['self'] + [format_field_name(field.name) for field in non_reserved_fields]),
                 cls.name + '.' + method.name,
                 )

            if len(non_reserved_fields) > 0:
                line('\n')
            for field in non_reserved_fields:
                if (field.label is not None) or (field.docs is not None):
                    line('        :param %s: %s\n', format_field_name(field.name),
                         to_docstring(field.label, field.docs, prefix=12, blank=False))



                line('        :type %s: %s (%s in AMQP)\n', format_field_name(field.name), TYPE_TRANSLATOR[field.basic_type], field.type)

            line('        """\n')

            for field in non_reserved_fields:
                line('        self.%s = %s\n', format_field_name(field.name), format_field_name(field.name))

            if len(non_reserved_fields) == 0:
                line('\n')

            # end
            if not is_content_static:
                from coolamqp.framing.compilation.textcode_fields import get_serializer, get_counter, get_from_buffer
                line('\n    def write_arguments(self, buf):\n')
                line(get_serializer(method.fields, 'self.', 2))

                line('    def get_size(self):\n')
                line(get_counter(method.fields, 'self.', 2))

            line('''\n    @staticmethod
    def from_buffer(buf, start_offset):
        offset = start_offset
''')

            line(get_from_buffer(method.fields, '', 2))
            line("        return %s(%s)",
                 full_class_name,
                 u', '.join(format_field_name(field.name) for field in method.fields if not field.reserved))

            line('\n\n')

        # Get me a dict - (classid, methodid) => class of method
        dct = {}
        for cls in get_classes(xml):
            for method in cls.methods:
                dct[((cls.index, method.index))] = '%s%s' % (name_class(cls.name), format_method_class_name(method.name))

    line('\nIDENT_TO_METHOD = {\n')
    for k, v in dct.items():
        line('    %s: %s,\n', repr(k), v)
    line('}\n\n')

    line('\nBINARY_HEADER_TO_METHOD = {\n')
    for k, v in dct.items():
        line('    %s: %s,\n', to_code_binary(struct.pack('!BB', *k)), v)
    line('}\n\n')

    line('\nCLASS_ID_TO_CONTENT_PROPERTY_LIST = {\n')
    for k,v in class_id_to_contentpropertylist.items():
        line('    %s: %s,\n', k, v)
    line('}\n\n')


    out.close()


if __name__ == '__main__':
    compile_definitions()
