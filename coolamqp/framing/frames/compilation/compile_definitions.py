from __future__ import division
from xml.etree import ElementTree
import collections
import struct
import six
import math

from coolamqp.framing.frames.compilation.utilities import get_constants, get_classes, get_domains, \
    byname, name_class, name_method, name_field, ffmt, doxify, infertype, normname, as_nice_escaped_string, \
    frepr
from coolamqp.framing.frames.base import BASIC_TYPES


def compile_definitions(xml_file='resources/amqp0-9-1.xml', out_file='coolamqp/framing/frames/definitions.py'):
    """parse resources/amqp-0-9-1.xml into """

    xml = ElementTree.parse(xml_file)
    out = open(out_file, 'wb')

    out.write('''# coding=UTF-8
from __future__ import print_function, absolute_import
"""
A Python version of the AMQP machine-readable specification.

Generated automatically by CoolAMQP from AMQP machine-readable specification.
See coolamqp.framing.frames.compilation for the tool

AMQP is copyright (c) 2016 OASIS
CoolAMQP is copyright (c) 2016 DMS Serwis s.c.
"""

import struct

from coolamqp.framing.frames.base_definitions import AMQPClass, AMQPMethodPayload, AMQPContentPropertyList
from coolamqp.framing.frames.field_table import enframe_table, deframe_table, frame_table_size

''')

    def line(data, *args, **kwargs):
        out.write(ffmt(data, *args, sane=True))

    # Output core ones
    FRAME_END = None
    con_classes = collections.defaultdict(list)
    line('# Core constants\n')
    for constant in get_constants(xml):
        if normname(constant.name) == 'FRAME_END':
            FRAME_END = constant.value
        g = ffmt('%s = %s', normname(constant.name), constant.value)
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
            con_classes[constant.kind].append(normname(constant.name))

    for constant_kind, constants in con_classes.items():
        line('\n%s = [%s]', normname(constant_kind), u', '.join(constants))

    # get domains
    domain_to_basic_type = {}
    line('\n\n\nDOMAIN_TO_BASIC_TYPE = {\n')
    for domain in get_domains(xml):
        line(u'    %s: %s,\n', frepr(domain.name), frepr(None if domain.elementary else domain.type))
        domain_to_basic_type[domain.name] = domain.type

    line('}\n')

    # Output classes
    for cls in get_classes(xml):

        cls = cls._replace(content_properties=[p._replace(basic_type=domain_to_basic_type[p.type]) for p in cls.content_properties])

        line('''\nclass %s(AMQPClass):
    """
    %s
    """
    NAME = %s
    INDEX = %s

''',
             name_class(cls.name), doxify(None, cls.docs), frepr(cls.name), cls.index)

        line('''\nclass %sContentPropertyList(AMQPContentPropertyList):
    """
    %s
    """
    CLASS_NAME = %s
    CLASS_INDEX = %s
    CLASS = %s

    CONTENT_PROPERTIES = [
    # tuple of (name, domain, type)
''',

           name_class(cls.name), doxify(None, cls.docs), frepr(cls.name), cls.index, name_class(cls.name))

        for property in cls.content_properties:
            line('        (%s, %s, %s), # %s\n', frepr(property.name), frepr(property.type), frepr(property.basic_type),
                 frepr(property.label))
        line('    ]\n\n')

        for method in cls.methods:
            full_class_name = '%s%s' % (name_class(cls.name), name_method(method.name))

            # annotate types
            method.fields = [field._replace(basic_type=domain_to_basic_type[field.type]) for field in method.fields]

            is_static = method.is_static()
            if is_static:
                static_size = method.get_size()

            is_content_static = len([f for f in method.fields if not f.reserved]) == 0

            line('''\nclass %s(AMQPMethodPayload):
    """
    %s
    """
    CLASS = %s
    NAME = %s
    CLASSNAME = %s
    FULLNAME = %s

    CONTENT_PROPERTY_LIST = %sContentPropertyList

    CLASS_INDEX = %s
    CLASS_INDEX_BINARY = %s
    METHOD_INDEX = %s
    METHOD_INDEX_BINARY = %s
    BINARY_HEADER = %s      # CLASS ID + METHOD ID

    SYNCHRONOUS = %s        # does this message imply other one?
    REPLY_WITH = [%s]

    SENT_BY_CLIENT = %s
    SENT_BY_SERVER = %s

    MINIMUM_SIZE = %s # arguments part can never be shorter than this

    IS_SIZE_STATIC = %s     # this means that argument part has always the same length
    IS_CONTENT_STATIC = %s  # this means that argument part has always the same content
''',
                 full_class_name,
                 doxify(method.label, method.docs),
                 name_class(cls.name),
                 frepr(method.name),
                 frepr(cls.name),
                 frepr(cls.name + '.' + method.name),
                 name_class(cls.name),
                 frepr(cls.index),
                 as_nice_escaped_string(chr(cls.index)),
                 frepr(method.index),
                 as_nice_escaped_string(chr(method.index)),
                 as_nice_escaped_string(chr(cls.index)+chr(method.index)),
                 repr(method.synchronous),
                 u', '.join([name_class(cls.name)+name_method(kidname) for kidname in method.response]),
                 repr(method.sent_by_client),
                 repr(method.sent_by_server),
                 repr(method.get_minimum_size(domain_to_basic_type)),
                 repr(is_static),
                 repr(is_content_static)
                 )


            if is_content_static:

                line('''    STATIC_CONTENT = %s  # spans LENGTH, CLASS ID, METHOD ID, ....., FRAME_END
''',
                     as_nice_escaped_string(struct.pack('!LBB', static_size+4, cls.index, method.index)+\
                                            method.get_static_body()+\
                                            struct.pack('!B', FRAME_END)))

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
                    line('\n        (%s, %s, %s, %s), ', frepr(field.name), frepr(field.type),
                         frepr(field.basic_type), repr(field.reserved))
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
                if (field.label is not None) or (field.docs is not None):
                    line('        :param %s: %s\n', name_field(field.name),
                         doxify(field.label, field.docs, prefix=12, blank=False))

                tp = {
                    'shortstr': 'binary type (max length 255)',
                    'longstr': 'binary type',
                    'table': 'table. See coolamqp.framing.frames.field_table',
                    'bit': 'bool',
                    'octet': 'int, 8 bit unsigned',
                    'short': 'int, 16 bit unsigned',
                    'long': 'int, 32 bit unsigned',
                    'longlong': 'int, 64 bit unsigned',
                    'timestamp': '64 bit signed POSIX timestamp (in seconds)',
                }

                line('        :type %s: %s (%s in AMQP)\n', name_field(field.name), tp[field.basic_type], field.type)

            line('        """\n')

            for field in non_reserved_fields:
                line('        self.%s = %s\n', name_field(field.name), name_field(field.name))

            if len(non_reserved_fields) == 0:
                line('\n')

            # end
            if not is_content_static:
                line('''\n    def write_arguments(self, buf):
''')
                def emit_structs(su):
                    if len(su) == 0:
                        return
                    line("        buf.write(struct.pack('!")
                    line(''.join(a for a, b in su))
                    line("', ")
                    line(', '.join(b for a, b in su))
                    line('))\n')

                def emit_bits(bits):
                    bits = [b for b in bits if b != '0']    # reserved values are out :>

                    line("        buf.write(struct.pack('!B', %s))\n",
                         u' | '.join((u'(int(%s) << %s)' % (bit, position)) for position, bit in enumerate(bits))
                         )

                good_structs = []
                written = False
                bits = []
                for field in method.fields:
                    val = 'self.' + name_field(field.name) if not field.reserved else BASIC_TYPES[field.basic_type][2]

                    if (len(bits) == 8) or ((field.basic_type != 'bit') and len(bits) > 0):
                        emit_bits(bits)
                        bits = []
                        written = True

                    if field.basic_type == 'bit':
                        bits.append(val)
                    elif field.reserved:
                        line("        buf.write("+BASIC_TYPES[field.basic_type][2]+")\n")
                        written = True
                        continue
                    elif BASIC_TYPES[field.basic_type][1] is None:
                        # struct can't do it

                        if field.basic_type == 'longstr':
                            good_structs.append(('L', 'len(%s)' % (val, )))

                        elif field.basic_type == 'shortstr':
                            good_structs.append(('B', 'len(%s)' % (val, )))

                        emit_structs(good_structs)
                        good_structs = []

                        if field.basic_type == 'table':
                            line('        enframe_table(buf, %s)\n' % (val, ))
                            written = True
                        else:
                            # emit ours
                            line('        buf.write('+val+')\n')
                            written = True
                    else:
                        # special case - empty string
                        if field.basic_type == 'shortstr' and field.reserved:
                            continue    # just skip :)

                        val = ('self.'+name_field(field.name)) if not field.reserved else frepr(BASIC_TYPES[field.basic_type][2], sop=six.binary_type)

                        good_structs.append((BASIC_TYPES[field.basic_type][1], val))
                        written = True
                written = written or len(good_structs) > 0
                emit_structs(good_structs)
                if len(bits) > 0:
                    emit_bits(bits)
                    written = True
                    bits = []

                if not written:
                    line('        pass # this has a frame, but it''s only default shortstrs\n')
                line('\n')

                line('    def get_size(self):\n        return ')
                parts = []
                accumulator = 0
                bits = 0
                for field in method.fields:
                    bt = field.basic_type

                    if (bits > 0) and (bt != 'bit'):    # sync bits if not
                        accumulator += int(math.ceil(bits / 8))
                        bits = 0

                    if field.basic_type == 'bit':
                        bits += 1
                    elif field.reserved:
                        accumulator += BASIC_TYPES[field.basic_type][3]
                    elif BASIC_TYPES[bt][0] is not None:
                        accumulator += BASIC_TYPES[field.basic_type][0]
                    elif bt == 'shortstr':
                        parts.append('len(self.'+name_field(field.name)+')')
                        accumulator += 1
                    elif bt == 'longstr':
                        parts.append('len(self.'+name_field(field.name)+')')
                        accumulator += 4
                    elif bt == 'table':
                        parts.append('frame_table_size(self.'+name_field(field.name)+')')
                        accumulator += 4
                    else:
                        raise Exception()

                if bits > 0:    # sync bits
                    accumulator += int(math.ceil(bits / 8))
                    bits = 0

                parts.append(repr(accumulator))
                line(u' + '.join(parts))
                line('\n')
            else:
                line('    # not generating write_arguments - this method has static content!\n')
            line('\n')

            line('''    @staticmethod
    def from_buffer(buf, start_offset):
''',
                 full_class_name)

            if is_content_static:
                line("        return %s()\n\n", full_class_name)
            else:
                line("""        assert (len(buf) - start_offset) >= %s.MINIMUM_SIZE, 'Frame too short!'
        offset = start_offset   # we will use it to count consumed bytes
""",
                     full_class_name)
                # The simple, or the painful way?
                has_nonstruct_fields = False
                for field in method.fields:
                    if BASIC_TYPES[field.basic_type][1] is None:
                        has_nonstruct_fields = True

                if len(method.fields) == 0:
                    line('        return %s(), 0\n', full_class_name)
                elif is_static:
                    fieldnames = []
                    formats = []

                    bits = []
                    bit_id = 0
                    bits_to_sync_later = {} # bit_0 => [fLSB, fMSB]

                    for field in method.fields:
                        if field.basic_type == 'bit':
                            bits.append(None if field.reserved else name_field(field.name))

                            if len(bits) == 8:
                                fieldnames.append('_bit_%s' % (bit_id, ))
                                formats.append('B')
                                bits_to_sync_later['_bit_%s' % (bit_id, )] = bits
                                bits = []
                                bit_id += 1

                        elif field.reserved:
                            formats.append('%sx' % (BASIC_TYPES[field.basic_type][0],))
                        else:
                            fieldnames.append(name_field(field.name))
                            formats.append(BASIC_TYPES[field.basic_type][1])

                    # sync bits
                    if len(bits) > 0:
                        fieldnames.append('_bit_%s' % (bit_id,))
                        formats.append('B')
                        bits_to_sync_later['_bit_%s' % (bit_id,)] = bits

                    line("        %s, = struct.unpack_from('!%s', buf, offset)\n",
                         u', '.join(fieldnames),
                         u''.join(formats)
                         )

                    # If there were any bits, unpack them now
                    for var_name, bits in bits_to_sync_later.items():
                        for bitname, multiplier in zip(bits, (1, 2, 4, 8, 16, 32, 64, 128)):
                            line("        %s = bool(%s & %s)\n", bitname, var_name, multiplier)


                    line("        return %s(%s)", full_class_name, u', '.join([
                        name_field(field.name) for field in method.fields if not field.reserved
                                                                                  ]))

                else:
                    def emit_bits(bits):

                        if all(n == '_' for n in bits):
                            # everything is reserved, lol
                            line("""        offset += 1
""")
                            return

                        line("""        _bit, = struct.unpack_from('!B', buf, offset)
        offset += 1
""")
                        for bit, multiplier in zip(bits, (1,2,4,8,16,32,64,128)):
                            if bit != '_':
                                line("""        %s = bool(_bit & %s)
""",
                                     bit, multiplier)

                    def emit_structures(ss, ln):
                        line("""        %s, = struct.unpack_from('!%s', buf, offset)
        offset += %s
""",
                             u', '.join([a[0] for a in ss if not (a[0] == '_' and a[1][-1] == 'x')]),
                             ''.join([a[1] for a in ss]),
                             ln
                             )

                    # we'll be counting bytes
                    to_struct = []  # accumulate static field, (var name, struct_code)
                    cur_struct_len = 0  # length of current struct

                    bits = []
                    bit_id = 0

                    for field in method.fields:
                        fieldname = '_' if field.reserved else name_field(field.name)

                        if (len(bits) > 0) and (field.basic_type != 'bit'):
                            emit_bits(bits)
                            bits = []

                        # offset is current start
                        # length is length to read
                        if BASIC_TYPES[field.basic_type][0] is not None:
                            if field.reserved:
                                to_struct.append(('_', '%sx' % (BASIC_TYPES[field.basic_type][0],)))
                            else:
                                to_struct.append((fieldname, BASIC_TYPES[field.basic_type][1]))
                            cur_struct_len += BASIC_TYPES[field.basic_type][0]
                        elif field.basic_type == 'bit':
                            bits.append(fieldname)
                        else:
                            if field.basic_type == 'table': # oh my god
                                line("""        %s, delta = deframe_table(buf, offset)
        offset += delta
""", name_field(field.name))
                            else:   # longstr or shortstr
                                f_q, f_l = ('L', 4) if field.basic_type == 'longstr' else ('B', 1)
                                to_struct.append(('s_len', f_q))
                                cur_struct_len += f_l
                                emit_structures(to_struct, cur_struct_len)
                                to_struct, cur_struct_len = [], 0
                                if field.reserved:
                                    line("        offset += s_len\n")
                                else:
                                    line("        %s = buf[offset:offset+s_len]\n        offset += s_len\n",
                                         fieldname)

                        # check bits for overflow
                        if len(bits) == 8:
                            emit_bits(bits)
                            bits = []

                    if len(bits) > 0:
                        emit_bits(bits)
                    elif len(to_struct) > 0:
                        emit_structures(to_struct, cur_struct_len)



                    line("        return %s(%s)",
                         full_class_name,
                         u', '.join(name_field(field.name) for field in method.fields if not field.reserved))


                line('\n\n')


        # Get me a dict - (classid, methodid) => class of method
        dct = {}
        for cls in get_classes(xml):
            for method in cls.methods:
                dct[((cls.index, method.index))] = '%s%s' % (name_class(cls.name), name_method(method.name))

    line('\nIDENT_TO_METHOD = {\n')
    for k, v in dct.items():
        line('    %s: %s,\n', repr(k), v)
    line('}\n\n')

    line('\nBINARY_HEADER_TO_METHOD = {\n')
    for k, v in dct.items():
        line('    %s: %s,\n', as_nice_escaped_string(struct.pack('!BB', *k)), v)
    line('}\n\n')


    out.close()


if __name__ == '__main__':
    compile_definitions()
