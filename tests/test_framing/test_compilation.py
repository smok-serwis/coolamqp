# coding=UTF-8
from __future__ import print_function, absolute_import, division
import six
import unittest


class TestCompilation(unittest.TestCase):
    def test_comp(self):
        from coolamqp.framing.compilation.compile_definitions import compile_definitions
        compile_definitions(xml_file='resources/amqp0-9-1.extended.xml', out_file='/tmp/definitions.py')
        
