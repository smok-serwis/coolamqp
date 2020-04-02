# coding=UTF-8
"""
Return Python code used to serialize/unserialize/get_size of lists of fields.

If you are going to paste the code you get here, note you nede to paste it into
a module that has following ok:

    * local variables denoted with a list of Field (namedtuple) with optional prefix exist
    * function header was already emitted
    * indent_level is in multiple of fours
    * following imports exists:
        * import struct
        * from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size
    * local variables buf and offset exist
    * local variable start_offset can be created

"""
from __future__ import absolute_import, division, print_function

import math

from coolamqp.framing.base import BASIC_TYPES
from coolamqp.framing.compilation.utilities import format_field_name


def get_counter(fields, prefix=u'', indent_level=2):
    """
    Emit code that counts how long this struct is.

    :param fields: list of Field instances
    :param prefix: pass "self." is inside a class
    :param indent_level: amount of tabs
    :return: block of code that does that
    """

    parts = []
    accumulator = 0
    bits = 0
    for field in fields:
        bt = field.basic_type
        nam = prefix + format_field_name(field.name)

        if (bits > 0) and (bt != 'bit'):  # sync bits if not
            accumulator += int(math.ceil(bits / 8))
            bits = 0

        if field.basic_type == 'bit':
            bits += 1
        elif field.reserved:
            accumulator += BASIC_TYPES[field.basic_type][3]
        elif BASIC_TYPES[bt][0] is not None:
            accumulator += BASIC_TYPES[field.basic_type][0]
        elif bt == 'shortstr':
            parts.append('len(' + nam + ')')
            accumulator += 1
        elif bt == 'longstr':
            parts.append('len(' + nam + ')')
            accumulator += 4
        elif bt == 'table':
            parts.append('frame_table_size(' + nam + ')')
            accumulator += 0  # because frame_table_size accounts for that 4 leading bytes
        else:
            raise Exception()

    if bits > 0:  # sync bits
        accumulator += int(math.ceil(bits / 8))

    return (u'    ' * indent_level) + u'return ' + (
        u' + '.join([str(accumulator)] + parts)) + u'\n'


# type: (...) -> tp.Tuple[str, dict]
def get_from_buffer(fields, prefix='', indent_level=2, remark=False):
    """
    Emit code that collects values from buf:offset, updating offset as progressing.
    :param remark: BE FUCKING VERBOSE! #DEBUG
    """
    code = []
    structers = {}

    def emit(fmt, *args):
        args = list(args)
        code.append(u'    ' * indent_level)
        assert fmt.count('%s') == len(args)
        for arg in args:
            fmt = fmt.replace('%s', str(arg), 1)
        code.append(fmt)
        code.append('\n')

    # actually go and load it

    bits = []
    ln = {'ln': 0}  # so I can modify from outside
    to_struct = []

    def emit_bits():
        if len(bits) == 0:
            return
        if remark:
            print('Bits are being banged')
        if all(n == '_' for n in bits):
            # everything is reserved, lol
            emit('offset += 1')
        else:
            to_struct.append(('_bit', 'B'))
            emit_structures(dont_do_bits=True)

            for multiplier, bit in enumerate(bits):
                if bit != '_':
                    emit("%s = bool(_bit >> %s)", bit, multiplier)
            emit('offset += 1')

        del bits[:]

    def emit_structures(dont_do_bits=False):  # type: (bool) -> dict
        if not dont_do_bits:
            emit_bits()
        if len(to_struct) == 0:
            return {}
        fffnames = [a for a, b in to_struct if a != u'_']  # skip reserved
        ffffmts = [b for a, b in to_struct]
        fmts = u''.join(ffffmts)
        emit("%s, = STRUCT_%s.unpack_from(buf, offset)",
             u', '.join(fffnames), fmts)
        emit("offset += %s", ln['ln'])
        ln['ln'] = 0
        del to_struct[:]
        return {fmts: fmts}

    for field in fields:
        fieldname = prefix + format_field_name(field.name)

        if (len(bits) > 0) and (field.basic_type != u'bit'):
            emit_bits()

        if remark:
            print('Doing', fieldname, 'of type', field.basic_type)

        # offset is current start
        # length is length to read
        if BASIC_TYPES[field.basic_type][0] is not None:
            # static type shit has

            assert len(bits) == 0

            if field.reserved:
                to_struct.append(
                    (u'_', '%sx' % (BASIC_TYPES[field.basic_type][0],)))
            else:
                to_struct.append((fieldname, BASIC_TYPES[field.basic_type][1]))

            ln['ln'] += BASIC_TYPES[field.basic_type][0]
        elif field.basic_type == u'bit':
            bits.append('_' if field.reserved else fieldname)
        elif field.basic_type == u'table':  # oh my god
            structers.update(emit_structures())

            assert len(bits) == 0
            assert len(to_struct) == 0

            emit("%s, delta = deframe_table(buf, offset)", fieldname)
            emit("offset += delta")
        else:  # longstr or shortstr
            f_q, f_l = ('L', 4) if field.basic_type == u'longstr' else ('B', 1)
            to_struct.append(('s_len', f_q))
            ln['ln'] += f_l
            structers.update(emit_structures())
            if field.reserved:
                emit("offset += s_len # reserved field!")
            else:
                emit("%s = buf[offset:offset+s_len]", fieldname)
                emit("offset += s_len")

        # check bits for overflow
        if len(bits) == 8:
            emit_bits()

    structers.update(emit_structures())

    return u''.join(code), structers


def get_serializer(fields, prefix='', indent_level=2):  # type: (list, str) -> str, dict
    """
    Emit code that serializes the fields into buf at offset

    :param fields: list of Field instances
    :param prefix: pass "self." is inside a class
    :return: block of code that does that, dictionary of struct-ers
    """
    code = []
    structers = {}

    def emit(fmt, *args):
        args = list(args)
        code.append(u'    ' * indent_level)
        while len(args) > 0:
            fmt = fmt.replace('%s', args[0], 1)
            del args[0]
        code.append(fmt)
        code.append('\n')

    formats = []
    format_args = []
    bits = []

    def emit_bits():
        p = []
        formats.append('B')
        if all(bit_name == 'False' for bit_name in bits):
            format_args.append('0')
        else:
            for bit_name, modif in zip(bits, range(8)):
                if bit_name != 'False':
                    p.append('(' + bit_name + ' << %s)' % (
                        modif,))  # yes you can << bools
            format_args.append(u' | '.join(p))
        del bits[:]

    def emit_single_struct_pack():
        formats_str = u''.join(formats)
        if formats_str not in structers:
            structers[formats_str] = formats_str
        emit("buf.write(STRUCT_%s.pack(%s))", formats_str,
             u', '.join(format_args))
        del formats[:]
        del format_args[:]

    for field in fields:
        nam = prefix + format_field_name(field.name)

        if (len(bits) == 8) or ((len(bits) > 0) and field.basic_type != 'bit'):
            emit_bits()

        if field.basic_type == 'bit':
            if field.reserved:
                bits.append("False")
            else:
                bits.append(nam)
        elif field.reserved:
            # Just pasta
            emit('buf.write(%s)', BASIC_TYPES[field.basic_type][2])
        else:
            if field.basic_type in ('shortstr', 'longstr'):
                formats.append('B' if field.basic_type == 'shortstr' else 'I')
                format_args.append('len(' + nam + ')')
                emit_single_struct_pack()
                emit('buf.write(%s)', nam)
            elif field.basic_type == 'table':
                if len(bits) > 0:
                    emit_bits()
                if len(formats) > 0:
                    emit_single_struct_pack()
                emit('enframe_table(buf, %s)', nam)
            else:
                formats.append(BASIC_TYPES[field.basic_type][1])
                format_args.append(nam)

    if len(bits) > 0:
        emit_bits()
    if len(formats) > 0:
        emit_single_struct_pack()

    emit('')  # eol

    return u''.join(code), structers
