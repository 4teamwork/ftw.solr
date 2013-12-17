from ftw.solr.patches.utils import isSimpleSearch
from unittest import TestCase


class TestIsSimpleSearch(TestCase):

    def test_is_simple_search_considers_anyting_with_quotes_not_simple(self):
        self.assertTrue(isSimpleSearch('foo'))
        self.assertTrue(isSimpleSearch('foo bar'))
        self.assertFalse(isSimpleSearch('"bar"'))
        self.assertFalse(isSimpleSearch('foo "bar"'))
        self.assertFalse(isSimpleSearch('foo"bar'))
