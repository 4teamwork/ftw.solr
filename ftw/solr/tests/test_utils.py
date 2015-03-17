from ftw.solr.patches.utils import isSimpleSearch
from ftw.solr.patches.utils import isSimpleTerm
from unittest import TestCase


class TestIsSimpleSearch(TestCase):

    def test_is_simple_search_considers_anyting_with_quotes_not_simple(self):
        self.assertTrue(isSimpleSearch('foo'))
        self.assertTrue(isSimpleSearch('foo bar'))
        self.assertFalse(isSimpleSearch('"bar"'))
        self.assertFalse(isSimpleSearch('foo "bar"'))
        self.assertFalse(isSimpleSearch('foo"bar'))

    def test_simple_searches_may_contain_dots(self):
        self.assertTrue(isSimpleSearch('foo.bar'))
        self.assertTrue(isSimpleSearch('foo.bar baz'))


class TestIsSimpleTerm(TestCase):

    def test_simple_terms_may_contain_dots(self):
        self.assertTrue(isSimpleTerm('foo.bar'))

    def test_simple_terms_may_contain_digits(self):
        self.assertTrue(isSimpleTerm('foo7bar'))
        self.assertTrue(isSimpleTerm('foo7'))
