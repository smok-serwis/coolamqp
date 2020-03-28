# coding=UTF-8
from __future__ import absolute_import, division, print_function

"""Generate serializers/unserializers/length getters for given property_flags"""
import six
import struct
import logging
from coolamqp.framing.compilation.textcode_fields import get_counter, \
    get_from_buffer, get_serializer

logger = logging.getLogger(__name__)

INIT_I = u'\n    def __init__(self, %s):\n'
SLOTS_I = u'\n    __slots__ = (%s)\n'
FROM_BUFFER_1 = u'    def from_buffer(cls, buf, start_offset):\n        ' \
                u'offset = start_offset + %s\n'
ASSIGN_A = u'        self.%s = %s\n'
STARTER = u'''from coolamqp.framing.base import AMQPContentPropertyList

class ParticularContentTypeList(AMQPContentPropertyList):
    """
    For fields:
'''
ZPF_S = u'''
    # A value for property flags that is used, assuming all bit fields are FALSE (0)
    ZERO_PROPERTY_FLAGS = %s
'''
NB = u"raise NotImplementedError('I don't support bits in properties')"
INTER_X = u'    * %s::%s'
BUF_WRITE_A = u'\n    def write_to(self, buf):\n        buf.write('
RESERVED = u' (reserved)'
UNICO = u"u'%s'"
SPACER = u'''
    """
'''
GET_SIZE_HEADER = u'\n    def get_size(self):\n'


def _compile_particular_content_property_list_class(zpf, fields):
    """
    Compile a particular content property list.

    Particularity stems from
    :param zpf: zero property list, as bytearray
    :param fields: list of all possible fields in this content property
    """
    from coolamqp.framing.compilation.utilities import format_field_name

    structers = {}

    if any(field.basic_type == 'bit' for field in fields):
        return NB

    # Convert ZPF to a list of [if_exists::bool]
    even = True
    zpf_bits = []
    for q in bytearray(zpf):
        p = bin(q)[2:]
        p = (u'0' * (8 - len(p))) + p

        if not even:
            p = p[:7]

        for x in p:
            zpf_bits.append(bool(int(x)))

    zpf_length = len(zpf)

    # 1 here does not mean that field is present. All bit fields are present,
    # but 0 in a ZPF. Fix this.
    zpf_bits = [zpf_bit or field.type == 'bit' for zpf_bit, field in
                zip(zpf_bits, fields)]

    mod = [STARTER]

    for field in fields:
        mod.append(
            INTER_X % (format_field_name(field.name), field.type))
        if field.reserved:
            mod.append(RESERVED)
        mod.append(u'\n')

    x = repr(six.binary_type(zpf))
    if not x.startswith('b'):
        x = 'b' + x

    present_fields = [field for field, present in zip(fields, zpf_bits) if
                      present]

    mod.append(SPACER)

    if len(present_fields) == 0:
        slots = u''
    else:
        slots = (u', '.join(
            (UNICO % format_field_name(field.name) for field in
             present_fields))) + u', '

    mod.append(SLOTS_I % slots)

    mod.append(ZPF_S % (x,))

    FFN = u', '.join(format_field_name(field.name) for field in present_fields)

    if len(present_fields) > 0:
        mod.append(INIT_I % (FFN,))

    for field in present_fields:
        mod.append(ASSIGN_A.replace(u'%s', format_field_name(
            field.name)))

    # Let's do write_to
    mod.append(BUF_WRITE_A)
    repred_zpf = repr(zpf)
    if not repred_zpf.startswith(u'b'):
        repred_zpf = u'b' + repred_zpf
    mod.append(repred_zpf)
    mod.append(u')\n')

    line, new_structers = get_serializer(present_fields, prefix=u'self.', indent_level=2)
    structers.update(new_structers)
    mod.append(line)

    # from_buffer
    # note that non-bit values
    mod.append(u'    @classmethod\n')
    mod.append(
        FROM_BUFFER_1 % (
            zpf_length,))
    line, new_structers = get_from_buffer(
        present_fields
        , prefix='', indent_level=2)
    structers.update(new_structers)
    mod.append(line)
    mod.append(u'        return cls(%s)\n' % (FFN,))

    # get_size
    mod.append(GET_SIZE_HEADER)
    mod.append(get_counter(present_fields, prefix=u'self.', indent_level=2)[
               :-1])  # skip eol
    mod.append(u' + %s\n' % (zpf_length,))  # account for pf length

    return u''.join(mod), structers


STRUCTERS_FOR_NOW = {}      # type: tp.Dict[str, struct.Struct]


def compile_particular_content_property_list_class(zpf, fields):
    from coolamqp.framing.base import AMQPContentPropertyList
    global STRUCTERS_FOR_NOW

    q, structers = _compile_particular_content_property_list_class(zpf, fields)
    locals_ = {
        'AMQPContentPropertyList': AMQPContentPropertyList
    }
    for structer in structers:
        if structer not in STRUCTERS_FOR_NOW:
            STRUCTERS_FOR_NOW[structer] = struct.Struct('!%s' % (structer,))

        locals_['STRUCT_%s' % (structer, )] = STRUCTERS_FOR_NOW[structer]

    loc = dict(globals(), **locals_)
    exec (q, loc)
    return loc['ParticularContentTypeList']
