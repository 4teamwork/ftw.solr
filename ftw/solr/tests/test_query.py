# -*- coding: utf-8 -*-
from ftw.solr.interfaces import ISolrSettings
from ftw.solr.query import escape
from ftw.solr.query import is_simple_search
from ftw.solr.query import make_query
from ftw.solr.query import split_simple_search
from plone.registry import Registry
from plone.registry.fieldfactory import persistentFieldAdapter
from plone.registry.interfaces import IRegistry
from plone.testing import zca
from zope.component import provideAdapter
from zope.component import provideUtility
import unittest


class TestQueryHelpers(unittest.TestCase):

    def test_escape(self):
        self.assertEqual(escape('foo!'), 'foo\\!')
        self.assertEqual(escape('1:1'), '1\\:1')
        self.assertEqual(escape('/path/to/a/file'), '\\/path\\/to\\/a\\/file')

    def test_is_simple_search(self):
        self.assertTrue(is_simple_search('foo'))
        self.assertTrue(is_simple_search('foo bar'))
        self.assertTrue(is_simple_search('"foo bar"'))
        self.assertTrue(is_simple_search('foo "bar foobar" baz'))
        self.assertTrue(is_simple_search('"foo AND bar"'))
        self.assertTrue(is_simple_search('foo "AND" bar'))
        self.assertTrue(is_simple_search('foo"'))

        self.assertFalse(is_simple_search('foo AND bar'))
        self.assertFalse(is_simple_search('foo OR bar'))
        self.assertFalse(is_simple_search('"foo bar" OR baz'))

    def test_split_simple_search(self):
        self.assertEqual(split_simple_search('foo'), ['foo'])
        self.assertEqual(split_simple_search('foo bar'), ['foo', 'bar'])
        self.assertEqual(split_simple_search('"foo bar"'), ['"foo bar"'])
        self.assertEqual(
            split_simple_search('foo "bar foobar" baz'),
            ['foo', '"bar foobar"', 'baz'])


class TestMakeQuery(unittest.TestCase):

    layer = zca.UNIT_TESTING

    def setUp(self):
        provideAdapter(persistentFieldAdapter)
        registry = Registry()
        registry.registerInterface(ISolrSettings)
        provideUtility(registry, IRegistry)
        self.settings = registry.forInterface(ISolrSettings)
        self.settings.simple_search_term_pattern = (
            u'Title:{term}^10 OR SearchableText:{term} OR '
            u'SearchableText:{term}*')
        self.settings.simple_search_phrase_pattern = (
            u'Title:"{phrase}"^20 OR SearchableText:"{phrase}"^5 OR '
            u'SearchableText:"{phrase}*"^2')
        self.settings.complex_search_pattern = (
            u'Title:({phrase})^10 OR SearchableText:({phrase})')
        self.settings.local_query_parameters = u''

    def test_single_search_word(self):
        self.assertEqual(
            make_query('foo'),
            u'Title:foo^10 OR SearchableText:foo OR SearchableText:foo*')

    def test_multiple_search_words(self):
        self.assertEqual(
            make_query('foo bar baz'),
            u'(Title:"foo bar baz"^20 OR SearchableText:"foo bar baz"^5 OR '
            u'SearchableText:"foo bar baz*"^2) OR ('
            u'(Title:foo^10 OR SearchableText:foo OR SearchableText:foo*) AND '
            u'(Title:bar^10 OR SearchableText:bar OR SearchableText:bar*) AND '
            u'(Title:baz^10 OR SearchableText:baz OR SearchableText:baz*))')

    def test_search_words_with_binary_operator(self):
        self.assertEqual(
            make_query('foo AND bar'),
            u'Title:(foo AND bar)^10 OR SearchableText:(foo AND bar)')

    def test_search_word_with_special_chars(self):
        self.assertEqual(
            make_query('C++'),
            u'(Title:"C\\+\\+"^20 OR SearchableText:"C\\+\\+"^5 OR '
            u'SearchableText:"C\\+\\+*"^2) OR '
            u'(Title:C\\+\\+^10 OR SearchableText:C\\+\\+ OR '
            u'SearchableText:C\\+\\+*)')

    def test_query_with_local_parameters(self):
        self.settings.local_query_parameters = (
            u'{!boost b=recip(ms(NOW,modified),3.858e-10,10,1)}')
        self.assertEqual(
            make_query('foo'),
            u'{!boost b=recip(ms(NOW,modified),3.858e-10,10,1)}'
            u'Title:foo^10 OR SearchableText:foo OR SearchableText:foo*')

    def test_long_phrase_gets_truncated_to_10_terms(self):
        self.settings.simple_search_term_pattern = u'Title:{term}'
        self.settings.simple_search_phrase_pattern = u'Title:"{phrase}"'
        self.assertEqual(
            make_query(
                'one two three four five six seven eight nine ten eleven'),
            u'(Title:"one two three four five six seven eight nine ten '
            u'eleven") OR ((Title:one) AND (Title:two) AND (Title:three) AND '
            u'(Title:four) AND (Title:five) AND (Title:six) AND (Title:seven) '
            u'AND (Title:eight) AND (Title:nine) AND (Title:ten))')

    def test_query_string_is_unicode(self):
        self.assertTrue(isinstance(make_query('über'), unicode))
        self.assertTrue(isinstance(make_query(u'über'), unicode))
