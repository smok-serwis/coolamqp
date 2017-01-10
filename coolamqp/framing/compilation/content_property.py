# coding=UTF-8
from __future__ import absolute_import, division, print_function
"""Generate serializers/unserializers/length getters for given property_flags"""
import six
import struct
import logging
from coolamqp.framing.compilation.textcode_fields import get_counter, get_from_buffer, get_serializer
from coolamqp.framing.base import AMQPContentPropertyList
from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size


logger = logging.getLogger(__name__)


def _compile_particular_content_property_list_class(zpf, fields):
    """
    Compile a particular content property list.

    Particularity stems from
    :param zpf: zero property list, as bytearray
    :param fields: list of all possible fields in this content property
    """
    from coolamqp.framing.compilation.utilities import format_field_name

    if any(field.basic_type == 'bit' for field in fields):
        return u"raise NotImplementedError('I don't support bits in properties yet')"

    # Convert ZPF to a list of [if_exists::bool]
    even = True
    zpf_bits = []
    for q in bytearray(zpf):
        p = bin(q)[2:]
        p = (u'0' * (8 - len(p))) + p

        if not even:
            p = p[:7]

        zpf_bits.extend(map(lambda x: bool(int(x)), p))

    zpf_length = len(zpf)

    # 1 here does not mean that field is present. All bit fields are present, but 0 in a ZPF. Fix this.
    zpf_bits = [zpf_bit or field.type == 'bit' for zpf_bit, field in zip(zpf_bits, fields)]

    mod = [u'''class ParticularContentTypeList(AMQPContentPropertyList):
    """
    For fields:
''']

    for field in fields:
        mod.append(u'    * %s::%s' % (format_field_name(field.name), field.type))
        if field.reserved:
            mod.append(u' (reserved)')
        mod.append(u'\n')

    x = repr(six.binary_type(zpf))
    if not x.startswith('b'):
        x = 'b'+x

    present_fields = [field for field, present in zip(fields, zpf_bits) if present]

    mod.append(u'''
    """
''')

    if len(present_fields) == 0:
        slots = u''
    else:
        slots = (u', '.join((u"u'%s'" % format_field_name(field.name) for field in present_fields)))+u', '

    mod.append(u'''
    __slots__ = (%s)
''' % slots)

    mod.append(u'''
    # A value for property flags that is used, assuming all bit fields are FALSE (0)
    ZERO_PROPERTY_FLAGS = %s
''' % (x, ))

    if len(present_fields) > 0:
        mod.append(u'''
    def __init__(self, %s):
''' % (u', '.join(format_field_name(field.name) for field in present_fields)))

    for field in present_fields:
        mod.append(u'        self.%s = %s\n'.replace(u'%s', format_field_name(field.name)))

    # Let's do write_to
    mod.append(u'\n    def write_to(self, buf):\n')
    mod.append(u'        buf.write(')
    repred_zpf = repr(zpf)
    if not repred_zpf.startswith(u'b'):
        repred_zpf = u'b' + repred_zpf
    mod.append(repred_zpf)
    mod.append(u')\n')

    mod.append(get_serializer(present_fields, prefix=u'self.', indent_level=2))

    # from_buffer
    # note that non-bit values
    mod.append(u'    @classmethod\n')
    mod.append(u'    def from_buffer(cls, buf, start_offset):\n        offset = start_offset + %s\n' % (zpf_length, ))
    mod.append(get_from_buffer(
        present_fields
        , prefix='', indent_level=2))
    mod.append(u'        return cls(%s)\n' %
               u', '.join(format_field_name(field.name) for field in present_fields))


    # get_size
    mod.append(u'\n    def get_size(self):\n')
    mod.append(get_counter(present_fields, prefix=u'self.', indent_level=2)[:-1])    # skip eol
    mod.append(u' + %s\n' % (zpf_length, ))   # account for pf length

    return u''.join(mod)


def compile_particular_content_property_list_class(zpf, fields):
    q = _compile_particular_content_property_list_class(zpf, fields)
    logger.debug('Compiling\n%s', q)
    exec(q)
    return ParticularContentTypeList
