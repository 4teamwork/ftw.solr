# -*- coding: utf-8 -*-
from ftw.solr.browser.maintenance import ellipsified_join
import unittest


class TestEllipsifiedJoin(unittest.TestCase):

    def test_max_equal_to_item_length(self):
        self.assertEqual(
            'eins, zwo',
            ellipsified_join(['eins', 'zwo'], 2)
        )

    def test_max_smaller_than_item_length(self):
        self.assertEqual(
            'eins, ...',
            ellipsified_join(['eins', 'zwo'], 1)
        )

    def test_max_none(self):
        self.assertEqual(
            'eins, zwo, drei',
            ellipsified_join(['eins', 'zwo', 'drei'], None)
        )
