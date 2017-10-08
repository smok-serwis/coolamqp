# coding=UTF-8
from __future__ import print_function, absolute_import, division
import six
import logging


class _Required(object):
    """Only a placeholder to tell apart None default values from required fields"""

def nop(x):
    return x

__all__ = [
    '_name', '_docs', '_ComputedField', '_ValueField', '_SimpleField',
    '_docs_with_label'
]

class _Field(object):
    """Base field object"""

    def set(self, obj, elem):
        obj.__dict__[self.field_name] = self.find(elem)

    def __init__(self, field_name):
        self.field_name = field_name

    def find(self, elem):
        raise NotImplementedError('abstract')


class _ComputedField(_Field):
    """
    There's no corresponding XML attribute name - value must
    be computed from element
    """
    def __init__(self, field_name, find_fun):
        super(_ComputedField, self).__init__(field_name)
        self.find = find_fun


class _ValueField(_Field):
    """
    Can hide under a pick of different XML attribute names.
    Has a type, can have a default value.
    """
    def __init__(self, xml_names, field_name, field_type=nop,
                 default=_Required):
        if not isinstance(xml_names, tuple):
            xml_names = (xml_names, )
        self.xml_names = xml_names
        assert field_type is not None
        self.field_name = field_name
        self.field_type = field_type
        self.default = default

    def find(self, elem):
        return self.field_type(self._find(elem))

    def _find(self, elem):
        xmln = [xmln for xmln in self.xml_names if xmln in elem.attrib]

        if xmln:
            return elem.attri[xmln[0]]
        else:
            if self.default is _Required:
                raise TypeError('Did not find field %s in elem tag %s, looked for names %s' % (self.field_name, elem.tag, self.xml_names))
            else:
                return self.default


class _SimpleField(_ValueField):
    """XML attribute is the same as name, has a type and can be default"""
    def __init__(self, name, field_type=nop, default=_Required):
        super(_SimpleField, self).__init__(name, name, field_type, default)


def get_docs(elem, label):
    """Parse an XML element. Return documentation"""
    for kid in elem.getchildren():

        if kid.tag == 'rule':
            return get_docs(kid, False)

        s = kid.text.strip().split('\n')
        return u'\n'.join([u.strip() for u in s if len(u.strip()) > 0])

    if label:
        return elem.attrib.get('label', None)

_name = _SimpleField('name', six.text_type)
_docs = _ComputedField('docs', lambda elem: get_docs(elem, False))
_docs_with_label = _ComputedField('docs', lambda elem: get_docs(elem, True))


