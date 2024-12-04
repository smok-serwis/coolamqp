# coding=UTF-8
from __future__ import print_function, absolute_import, division
import sys
import logging
import unittest
import io
import warnings

from coolamqp.framing.definitions import QueueDeclare

from coolamqp.objects import NodeDefinition, MessageProperties, Queue, Exchange
from coolamqp.argumentify import argumentify

logger = logging.getLogger(__name__)
logging.getLogger('coolamqp').setLevel(logging.DEBUG)

IS_PY3 = sys.version.startswith('3')


class TestObjects(unittest.TestCase):

    def test_exchange_repr(self):
        xchg = Exchange()
        repr(xchg)
        queue = Queue(exchange=xchg)
        repr(queue)

        a = {xchg: 5, queue: 3}
        self.assertEqual(a[xchg], 5)
        self.assertEqual(a[queue], 3)

    def test_queue_failures(self):
        Queue()
        Queue('')
        self.assertRaises(ValueError, Queue, durable=True)
        self.assertRaises(ValueError, Queue, auto_delete=False, durable=True)
        self.assertRaises(ValueError, Queue, 'test', auto_delete=True, durable=True)
        self.assertRaises(ValueError, Queue, auto_delete=False)
        repr(Queue())

    def test_queue_repr(self):
        q = Queue('test')
        repr(q)

    @unittest.skipUnless(sys.version.startswith('3'), 'Needs Python 3.x')
    def test_queue_warns(self):
        warnings.resetwarnings()

        with warnings.catch_warnings(record=True) as w:
            Queue('test', auto_delete=True, exclusive=True)
            Queue(auto_delete=True, exclusive=False)
        logger.warning(repr(w))
        self.assertEqual(len(w), 2 if IS_PY3 else 1)
        self.assertTrue(issubclass(w[0].category, UserWarning))
        if IS_PY3:
            self.assertTrue(issubclass(w[1].category, DeprecationWarning))

    def test_headers(self):
        msg = MessageProperties(headers={'city': 'sydney'})
        buf = io.BytesIO()
        msg.write_to(buf)

    def test_queue_declare(self):
        args = argumentify({'x-dead-letter-exchange': 'deadletter',
                                           'x-message-ttl': 1000})
        qd = QueueDeclare(b'test', False, False, False, False, False, args)
        buf = io.BytesIO()
        qd.write_arguments(buf)
        buf = buf.getvalue()
        logger.warning(repr(buf))
        qd = QueueDeclare.from_buffer(buf, 0)
        self.assertEqual(qd.queue, b'test')

    def test_message_properties(self):
        empty_p_msg = MessageProperties()
        ce_p_msg = MessageProperties(content_encoding=b'wtf')
        self.assertIn('wtf', str(ce_p_msg))

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
