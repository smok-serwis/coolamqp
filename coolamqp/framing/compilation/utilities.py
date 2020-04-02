# coding=UTF-8
from __future__ import absolute_import, division, print_function

import six


# docs may be None


def as_unicode(clbl):
    def roll(*args, **kwargs):
        return six.text_type(clbl(*args, **kwargs))

    return roll


@as_unicode
def format_field_name(field):
    if field in (u'global', u'type'):
        field = field + '_'
    return field.replace('-', '_')
