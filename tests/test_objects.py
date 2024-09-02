# coding=UTF-8
from __future__ import print_function, absolute_import, division

import unittest
import sys

from coolamqp.objects import NodeDefinition, MessageProperties, Queue


class TestObjects(unittest.TestCase):
    def test_message_properties(self):
        empty_p_msg = MessageProperties()
        ce_p_msg = MessageProperties(content_encoding=b'wtf')
        self.assertIn('wtf', str(ce_p_msg))

    @unittest.skipIf(sys.platform.startswith('2'), 'Only Python 3 has assertWarns')
    def test_warning(self):
        with self.assertWarns(PendingDeprecationWarning):
            Queue(auto_delete=True, exclusive=False)

    def test_node_definition_from_amqp(self):
        n1 = NodeDefinition(u'amqp://ala:ma@kota/psa')

        self.assertEqual(n1.user, u'ala')
        self.assertEqual(n1.password, u'ma')
        self.assertEqual(n1.virtual_host, u'psa')
        self.assertEqual(n1.host, u'kota')

        n1 = NodeDefinition(u'amqp://ala:ma@kota/')

        self.assertEqual(n1.virtual_host, u'/')

    def test_get_message_properties(self):
        empty_p_msg = MessageProperties()
        ce_p_msg = MessageProperties(content_encoding=b'wtf')

        self.assertIsNone(empty_p_msg.get('content_encoding'), None)
        self.assertEqual(ce_p_msg.get('content_encoding', b'wtf'), b'wtf')
