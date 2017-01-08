# coding=UTF-8
"""
It sounds like a melody
"""
from __future__ import print_function, absolute_import, division
import six
import unittest


from coolamqp.attaches.utils import ManualConfirmableRejectable, AtomicTagger


class TestAtomicTagger(unittest.TestCase):

    def test_insertionOrder(self):
        at = AtomicTagger()

        a1 = at.get_key()
        a2 = at.get_key()
        a3 = at.get_key()

        at.deposit(a1, b'ABC')
        at.deposit(a3, b'GHI')
        at.deposit(a2, b'DEF')

        self.assertEquals(at.tags[0][1], b'ABC')
        self.assertEquals(at.tags[1][1], b'DEF')
        self.assertEquals(at.tags[2][1], b'GHI')

    def test_1(self):

        at = AtomicTagger()

        a1 = at.get_key()
        a2 = at.get_key()
        a3 = at.get_key()

        n1 = at.get_key()
        n2 = at.get_key()
        n3 = at.get_key()

        P = {'acked_P': False, 'nacked_P': False, 'acked_N': False, 'nacked_N': False}

        def assigner(nam, val=True):
            def x():
                P[nam] = val
            return x


        at.deposit(a2, ManualConfirmableRejectable(assigner('acked_P'), assigner('nacked_P')))
        at.deposit(n2, ManualConfirmableRejectable(assigner('acked_N'), assigner('nacked_N')))

        print(at.tags)

        at.ack(a3, True)
        at.nack(n3, True)

        self.assertTrue(P['acked_P'] and (not P['nacked_P']) and P['nacked_N'] and (not P['acked_N']))



        
