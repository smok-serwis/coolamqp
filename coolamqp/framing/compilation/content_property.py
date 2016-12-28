# coding=UTF-8
from __future__ import absolute_import, division, print_function
"""
Generate serializers/unserializers/length getters for given property_flags
"""

class ContentPropertyListCompiler(object):
    """
    This produces serializers, unserializers and size getters for any property_flags combinations.

    Sure you could do that by hand, but how much faster is it to have most common messages precompiled?
    """

    MAX_COMPILERS_TO_KEEP = 8

    def __init__(self, content_property_list_class):


def compile_for(fields):
    """Compile a serializer, unserializer and length calculator for a list of fields"""

    mod = u'''# coding=UTF-8
import struct
from coolamqp.framing.field_table import enframe_table, deframe_table, frame_table_size

def write_to(
'''