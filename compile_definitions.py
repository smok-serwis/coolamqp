from __future__ import division

import collections
import struct
import subprocess
from xml.etree import ElementTree

import math
import six

from coolamqp.framing.compilation.utilities import Constant, Class, \
    Domain, \
    name_class, format_method_class_name, format_field_name, ffmt, to_docstring, \
    pythonify_name, to_code_binary, \
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


def compile_definitions(xml_file='resources/amqp0-9-1.extended.xml',
                        out_file='coolamqp/framing/definitions.py'):
    """parse resources/amqp-0-9-1.xml into """

    xml = ElementTree.parse(xml_file)
    out = open(out_file, 'wb')

    out.write(u'''# coding=UTF-8
from __future__ import print_function, absolute_import
"""
A Python version of the AMQP machine-readable specification.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See coolamqp.uplink.framing.compilation for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016-2018 DMS Serwis s.c., 2018-2019 SMOK sp. z o.o.


###########################################################
# IMPORTANT NOTE                                          #
# Type of field may depend on the origin of packet.       #
# strings will be memoryviews if we received the packet   #
# while they may be bytes if we created it                #
#                                                         #
# this has some use - speed :D                            #
###########################################################
tl;dr - you received something and it's supposed to be a
binary string? It's a memoryview all right.
Only thing that isn't are field names in tables.
"""

import struct
import collections
import logging
import six
import typing as tp

from coolamqp.framing.base import AMQPClass, AMQPMethodPayload, AMQPContentPropertyList
from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size
from coolamqp.framing.compilation.content_property import compile_particular_content_property_list_class

logger = logging.getLogger(__name__)

Field = collections.namedtuple('Field', ('name', 'type', 'basic_type', 'reserved'))

'''.encode('utf8'))

    def line(data, *args, **kwargs):
        out.write(ffmt(data, *args, sane=True).encode('utf8'))

    # Output core ones
    FRAME_END = None
    con_classes = collections.defaultdict(list)
    line('# Core constants\n')
    was_linefeed_before = True
    for constant in Constant.findall(xml):
        if not was_linefeed_before:
            line('\n')
        was_docs_output = False
        if constant.docs:
            was_docs_output = True
            lines = constant.docs.split('\n')
            line(' # %s\n', lines[0])
            if len(lines) > 1:
                for ln in lines[1:]:
                    line(u' ' * len(g))
                    line(u' # %s\n', ln)
        if pythonify_name(constant.name) == 'FRAME_END':
            FRAME_END = constant.value
        g = ffmt('%s = %s\n', pythonify_name(constant.name), constant.value)
        line(g)
        if 0 <= constant.value <= 255:
            z = repr(six.int2byte(constant.value))
            if not z.startswith(u'b'):
                z = u'b' + z
            g = ffmt('%s_BYTE = %s\n', pythonify_name(constant.name), z)
            line(g)

        if was_docs_output:
            line('\n')
            was_linefeed_before = True
        else:
            was_linefeed_before = False

        if constant.kind:
            con_classes[constant.kind].append(pythonify_name(constant.name))

    for constant_kind, constants in con_classes.items():
        line('\n%sS = [%s]', pythonify_name(constant_kind),
             u', '.join(constants))

    # get domains
    domain_to_basic_type = {}
    line('\n\n\nDOMAIN_TO_BASIC_TYPE = {\n')
    for domain in Domain.findall(xml):
        line(u'    %s: %s,\n', frepr(domain.name),
             frepr(None if domain.elementary else domain.type))
        domain_to_basic_type[domain.name] = domain.type

    line('}\n')

    class_id_to_contentpropertylist = {}

    # below are stored as strings!
    methods_that_are_reply_reasons_for = {}  # eg. ConnectionOpenOk: ConnectionOk
    methods_that_are_replies_for = {}  # eg. ConnectionOk: [ConnectionOpenOk]

    # Output classes
    for cls in Class.findall(xml):

        cls.properties = [p._replace(basic_type=domain_to_basic_type[p.type]) for
                        p in cls.properties]

        line('''\nclass %s(AMQPClass):
    """
    %s
    """
    NAME = %s
    INDEX = %s

''',
             name_class(cls.name), to_docstring(None, cls.docs),
             frepr(cls.name), cls.index)

        if len(cls.properties) > 0:
            class_id_to_contentpropertylist[cls.index] = name_class(
                cls.name) + 'ContentPropertyList'

            line('''\nclass %sContentPropertyList(AMQPContentPropertyList):
    """
    %s
    """
    FIELDS = [
''',

                 name_class(cls.name), to_docstring(None, cls.docs),
                 frepr(cls.name), cls.index, name_class(cls.name))

            is_static = all(
                property.basic_type not in ('table', 'longstr', 'shortstr') for
                property in cls.properties)

            for property in cls.properties:
                if property.basic_type == 'bit':
                    raise ValueError('bit properties are not supported!'
                                     )
                line('        Field(%s, %s, %s, %s),\n', frepr(property.name),
                     frepr(property.type),
                     frepr(property.basic_type), repr(property.reserved))
            line('''    ]
    # A dictionary from a zero property list to a class typized with
    # some fields
    PARTICULAR_CLASSES = {}
\n''',
                 name_class(cls.name))

            if any(prop.basic_type == 'bit' for prop in cls.properties):
                raise NotImplementedError(
                    'I should emit a custom zero_property_list staticmethod :(')
            line(u'''    def __new__(self, **kwargs):
        """
        Return a property list.
''')
            property_strs = []

            my_props = [prop for prop in cls.properties if (not prop.reserved)]
            for property in my_props:
                line('        :param %s: %s\n',
                     format_field_name(property.name), property.label)
                line('        :type %s: %s (AMQP as %s)\n',
                     format_field_name(property.name),
                     TYPE_TRANSLATOR[property.basic_type], property.basic_type)
            line('        """\n')
            zpf_len = int(math.ceil(len(cls.properties) // 15))

            first_byte = True  # in 2-byte group
            piece_index = 7  # from 7 downto 0
            fields_remaining = len(cls.properties)

            byte_chunk = []
            line(u'        zpf = bytearray([\n')

            for field in cls.properties:
                # a bit
                if piece_index > 0:
                    if field.reserved or field.basic_type == 'bit':
                        pass  # zero anyway
                    else:
                        byte_chunk.append(u"(('%s' in kwargs) << %s)" % (
                        format_field_name(field.name), piece_index))
                    piece_index -= 1
                else:
                    if first_byte:
                        if field.reserved or field.basic_type == 'bit':
                            pass  # zero anyway
                        else:
                            byte_chunk.append(u"int('%s' in kwargs)" % (
                            format_field_name(field.name),))
                    else:
                        # this is the "do we need moar flags" section
                        byte_chunk.append(u"kwargs['%s']" % (
                            int(fields_remaining > 1)
                        ))

                    # Emit the byte
                    line(u'            %s,\n', u' | '.join(byte_chunk))
                    byte_chunk = []
                    first_byte = not first_byte
                    piece_index = 7
                fields_remaining -= 1

            if len(byte_chunk) > 0:
                line(u'            %s\n',
                     u' | '.join(byte_chunk))  # We did not finish

            line(u'        ])\n        zpf = six.binary_type(zpf)\n')
            line(u'''
#        If you know in advance what properties you will be using, use typized constructors like
#
#          runs once
#            my_type = BasicContentPropertyList.typize('content_type', 'content_encoding')
#
#           runs many times
#            props = my_type('text/plain', 'utf8')
#
#       instead of
#
#           # runs many times
#           props = BasicContentPropertyList(content_type='text/plain', content_encoding='utf8')
#
#       This way you will be faster.
#
#       If you do not know in advance what properties you will be using, it is correct to use
#       this constructor.
        if zpf in BasicContentPropertyList.PARTICULAR_CLASSES:
            return %s.PARTICULAR_CLASSES[zpf](**kwargs)
        else:
            logger.debug('Property field (%s:%d) not seen yet, compiling', repr(zpf))
            c = compile_particular_content_property_list_class(zpf, %s.FIELDS)
            %s.PARTICULAR_CLASSES[zpf] = c
            return c(**kwargs)
'''.replace('%s', name_class(cls.name) + 'ContentPropertyList').replace('%d',
                                                                        '%s'))

            line(u'''
    @staticmethod
    def typize(*fields):        # type: (*str) -> type
    ''')
            line(u'    zpf = bytearray([\n')

            first_byte = True  # in 2-byte group
            piece_index = 7  # from 7 downto 0
            fields_remaining = len(cls.properties)
            byte_chunk = []

            for field in cls.properties:
                # a bit
                if piece_index > 0:
                    if field.reserved or field.basic_type == 'bit':
                        pass  # zero
                    else:
                        byte_chunk.append(u"(('%s' in fields) << %s)" % (
                        format_field_name(field.name), piece_index))
                    piece_index -= 1
                else:
                    if first_byte:
                        if field.reserved or field.basic_type == 'bit':
                            pass  # zero
                        else:
                            byte_chunk.append(u"int('%s' in kwargs)" % (
                            format_field_name(field.name),))
                    else:
                        # this is the "do we need moar flags" section
                        byte_chunk.append(u"kwargs['%s']" % (
                            int(fields_remaining > 1)
                        ))

                    # Emit the byte
                    line(u'        %s,\n', u' | '.join(byte_chunk))
                    byte_chunk = []
                    first_byte = not first_byte
                    piece_index = 7
                fields_remaining -= 1

            if len(byte_chunk) > 0:
                line(u'        %s\n',
                     u' | '.join(byte_chunk))  # We did not finish

            line(u'''        ])
        zpf = six.binary_type(zpf)
        if zpf in %s.PARTICULAR_CLASSES:
            return %s.PARTICULAR_CLASSES[zpf]
        else:
            logger.debug('Property field (%s:%d) not seen yet, compiling', repr(zpf))
            c = compile_particular_content_property_list_class(zpf, %s.FIELDS)
            %s.PARTICULAR_CLASSES[zpf] = c
            return c
'''.replace("%s", name_class(cls.name) + 'ContentPropertyList').replace('%d',
                                                                        '%s'))

            line(u'''
    @staticmethod
    def from_buffer(buf, offset):    # type: (buffer, int) -> %s
        """
        Return a content property list instance unserialized from
        buffer, so that buf[offset] marks the start of property flags
        """
        # extract property flags
        pfl = 2
        if six.PY2:
            while ord(buf[offset + pfl - 1]) & 1:
                pfl += 2
        else:
            while buf[offset + pfl - 1] & 1:
                pfl += 2
        zpf = %s.zero_property_flags(buf[offset:offset+pfl]).tobytes()
        if zpf in %s.PARTICULAR_CLASSES:
            return %s.PARTICULAR_CLASSES[zpf].from_buffer(buf, offset)
        else:
            logger.debug('Property field (%s:%d) not seen yet, compiling', repr(zpf))
            c = compile_particular_content_property_list_class(zpf, %s.FIELDS)
            %s.PARTICULAR_CLASSES[zpf] = c
            return c.from_buffer(buf, offset)

'''.replace('%s', name_class(cls.name) + 'ContentPropertyList').replace("%d",
                                                                        "%s"))

        # ============================================ Do methods for this class
        for method in cls.methods:
            full_class_name = u'%s%s' % (
            name_class(cls.name), format_method_class_name(method.name))

            # annotate types
            method.fields = [
                field._replace(basic_type=domain_to_basic_type[field.type]) for
                field in method.fields]

            non_reserved_fields = [field for field in method.fields if
                                   not field.reserved]

            is_static = method.is_static()
            if is_static:
                static_size = get_size(method.fields)

            is_content_static = len(
                [f for f in method.fields if not f.reserved]) == 0

            if len(non_reserved_fields) == 0:
                slots = u''
            else:
                slots = (u', '.join(
                    map(lambda f: frepr(format_field_name(f.name)),
                        non_reserved_fields))) + u', '

            line('''\nclass %s(AMQPMethodPayload):
    """
    %s
    """
    __slots__ = (%s)

    NAME = %s

    INDEX = (%s, %s)          # (Class ID, Method ID)
    BINARY_HEADER = %s      # CLASS ID + METHOD ID

    SENT_BY_CLIENT, SENT_BY_SERVER = %s, %s

    IS_SIZE_STATIC = %s     # this means that argument part has always the same length
    IS_CONTENT_STATIC = %s  # this means that argument part has always the same content
''',

                 full_class_name,
                 to_docstring(method.label, method.docs),
                 slots,
                 frepr(cls.name + '.' + method.name),
                 frepr(cls.index), frepr(method.index),
                 to_code_binary(struct.pack("!HH", cls.index, method.index)),
                 repr(method.sent_by_client),
                 repr(method.sent_by_server),
                 repr(is_static),
                 repr(is_content_static)
                 )

            _namify = lambda x: name_class(cls.name) + format_method_class_name(
                x)

            methods_that_are_replies_for[full_class_name] = []
            for response in method.response:
                methods_that_are_reply_reasons_for[
                    _namify(response)] = full_class_name
                methods_that_are_replies_for[full_class_name].append(
                    _namify(response))

            if is_content_static:
                line('''    STATIC_CONTENT = %s  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END
''',
                     to_code_binary(
                         struct.pack('!LHH', static_size + 4, cls.index,
                                     method.index) + \
                         method.get_static_body() + \
                         struct.pack('!B', FRAME_END)))

            # fields
            if len(method.fields) > 0:
                line('\n    # See constructor pydoc for details\n')
                line('    FIELDS = [ \n')

                for field in method.fields:
                    line('        Field(%s, %s, %s, reserved=%s),\n',
                         frepr(field.name), frepr(field.type),
                         frepr(field.basic_type), repr(field.reserved))

                line('    ]\n')

            # __repr__
            line('''\n    def __repr__(self):       # type: () -> str
        """
        Convert the frame to a Python-representable string
        :return: Python string representation
        """
        return '%s(%S)' % (', '.join(map(repr, [%s])))\n''',
                 full_class_name,
                 u", ".join(['self.'+format_field_name(field.name) for field in non_reserved_fields]))

            # constructor
            line('''\n    def __init__(%s):
        """
        Create frame %s
''',
                 u', '.join(
                     ['self'] + [format_field_name(field.name) for field in
                                 non_reserved_fields]),
                 cls.name + '.' + method.name,
                 )

            if len(non_reserved_fields) > 0:
                line('\n')

            for field in non_reserved_fields:
                if (field.label is not None) or (field.docs is not None):
                    line('        :param %s: %s\n',
                         format_field_name(field.name),
                         to_docstring(field.label, field.docs, prefix=12,
                                      blank=False))

                line('        :type %s: %s (%s in AMQP)\n',
                     format_field_name(field.name),
                     TYPE_TRANSLATOR[field.basic_type], field.type)

            line('        """\n')

            for field in non_reserved_fields:
                line('        self.%s = %s\n', format_field_name(field.name),
                     format_field_name(field.name))

            if len(non_reserved_fields) == 0:
                line('\n')

            # end
            if not is_content_static:
                from coolamqp.framing.compilation.textcode_fields import \
                    get_serializer, get_counter, get_from_buffer
                line('\n    def write_arguments(self, buf):  # type: (tp.BinaryIO) -> None\n')
                line(get_serializer(method.fields, 'self.', 2))

                line('    def get_size(self):       # type: () -> int\n')
                line(get_counter(method.fields, 'self.', 2))

            line('''\n    @staticmethod
    def from_buffer(buf, start_offset):     # type: (buffer, int) -> %s
        offset = start_offset
''', full_class_name)

            line(get_from_buffer(method.fields, '', 2,
                                 remark=(method.name == 'deliver')))

            line("        return %s(%s)",
                 full_class_name,
                 u', '.join(
                     format_field_name(field.name) for field in method.fields if
                     not field.reserved))

            line('\n\n')

        # Get me a dict - (classid, methodid) => class of method
        dct = {}
        for cls in Class.findall(xml):
            for method in cls.methods:
                dct[((cls.index, method.index))] = '%s%s' % (
                    name_class(cls.name), format_method_class_name(method.name))

    line('\nIDENT_TO_METHOD = {\n')
    for k, v in dct.items():
        line('    %s: %s,\n', repr(k), v)
    line('}\n\n')

    line('\nBINARY_HEADER_TO_METHOD = {\n')
    for k, v in dct.items():
        line('    %s: %s,\n', to_code_binary(struct.pack('!HH', *k)), v)
    line('}\n\n')

    line('\nCLASS_ID_TO_CONTENT_PROPERTY_LIST = {\n')
    for k, v in class_id_to_contentpropertylist.items():
        line('    %s: %s,\n', k, v)
    line('}\n\n')

    line(u'''# Methods that are sent as replies to other methods, ie. ConnectionOpenOk: ConnectionOpen
# if a method is NOT a reply, it will not be in this dict
# a method may be a reply for AT MOST one method
REPLY_REASONS_FOR = {\n''')
    for k, v in methods_that_are_reply_reasons_for.items():
        line(u'    %s: %s,\n' % (k, v))

    line(u'''}

# Methods that are replies for other, ie. ConnectionOpenOk: ConnectionOpen
# a method may be a reply for ONE or NONE other methods
# if a method has no replies, it will have an empty list as value here
REPLIES_FOR = {\n''')

    for k, v in methods_that_are_replies_for.items():
        line(u'    %s: [%s],\n' % (k, u', '.join(map(str, v))))
    line(u'}\n')

    out.close()


if __name__ == '__main__':
    compile_definitions()
    proc = subprocess.run(['yapf', 'coolamqp/framing/definitions.py'], stdout=subprocess.PIPE)
    with open('coolamqp/framing/definitions.py', 'wb') as f_out:
        f_out.write(proc.stdout)
