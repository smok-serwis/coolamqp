# coding=UTF-8
"""
It sounds like a melody
"""
from __future__ import print_function, absolute_import, division

import unittest

from coolamqp.objects import NodeDefinition, MessageProperties


class TestObjects(unittest.TestCase):
    def test_node_definition_from_amqp(self):
        n1 = NodeDefinition(u'amqp://ala:ma@kota/psa')

        self.assertEquals(n1.user, u'ala')
        self.assertEquals(n1.password, u'ma')
        self.assertEquals(n1.virtual_host, u'psa')
        self.assertEquals(n1.host, u'kota')

        n1 = NodeDefinition(u'amqp://ala:ma@kota/')

        self.assertEquals(n1.virtual_host, u'/')

    def test_get_message_properties(self):
        empty_p_msg = MessageProperties()
        ce_p_msg = MessageProperties(content_encoding=b'wtf')

        self.assertIsNone(empty_p_msg.get('content_encoding'), None)
        self.assertEquals(ce_p_msg.get('content_encoding', b'wtf'), b'wtf')
