from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.manager import SolrConnectionConfig
from collective.solr.parser import SolrSchema, SolrField
from collective.solr.tests.utils import getData
from ftw.solr.patches.mangler import cleanupQueryParameters
from ftw.solr.patches.mangler import subtractQueryParameters
from ftw.solr.patches.mangler import leading_wildcards
from ftw.solr.patches.mangler import mangleQuery
from ftw.solr.patches.mangler import mangle_searchable_text_query
from ftw.solr.patches.mangler import searchterms_from_value
from ftw.solr.patches.mangler import trailing_wildcards
from unittest import TestCase
from zope.component import provideUtility, getUtility


class TestQueryMangler(TestCase):

    def setUp(self):
        provideUtility(SolrConnectionConfig(), ISolrConnectionConfig)
        xml = getData('plone_schema.xml')
        xml = xml[xml.find('<schema'):]
        self.schema = SolrSchema(xml.strip())

    def test_search_pattern_value_is_lowercase(self):
        config = getUtility(ISolrConnectionConfig)
        config.search_pattern = 'Title:{value}'

        query = dict(SearchableText='Pass')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['Title:pass'])},
            query
        )

        query = dict(SearchableText='Pass*')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['Title:pass'])},
            query
        )

        query = dict(SearchableText='Pass port')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['Title:(pass port)'])},
            query
        )

    def test_simple_terms_result_in_value_without_wildcards(self):
        config = getUtility(ISolrConnectionConfig)
        config.search_pattern = '{value}'

        query = dict(SearchableText='foo')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['foo'])},
            query
        )

    def test_simple_search_results_in_value_without_wildcards(self):
        config = getUtility(ISolrConnectionConfig)
        config.search_pattern = '{value}'

        query = dict(SearchableText='foo bar')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['(foo bar)'])},
            query
        )

    def test_complex_search_goes_through_unmodified(self):
        config = getUtility(ISolrConnectionConfig)
        config.search_pattern = '{irrelevant}'

        query = dict(SearchableText='foo AND bar')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': 'foo AND bar'},
            query
        )

    def test_simple_terms_are_handled_the_same_as_simple_searches(self):
        config = getUtility(ISolrConnectionConfig)
        config.search_pattern = '{value} OR {value_lwc} OR {value_twc}'

        # Simple term
        query = dict(SearchableText='foo')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['foo OR (*foo) OR (foo*)'])},
            query
        )

        # Simple search
        query = dict(SearchableText='foo bar')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(
                ['(foo bar) OR (*foo *bar) OR (foo* bar*)'])},
            query
        )


class TestMangleSearchableTextQuery(TestCase):

    def test_simple_terms_value_contains_no_wildcards(self):
        orig_query = 'foo'
        pattern = '{value}'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals(
            'foo',
            mangled_query)

    def test_simple_search_results_in_simple_pattern_substitution(self):
        orig_query = 'foo bar'
        pattern = '{value}'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals(
            '(foo bar)',
            mangled_query)

    def test_simple_search_substitutes_lwc_and_twc_values(self):
        orig_query = 'foo bar'
        pattern = '{value_lwc} OR {value_twc}'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals(
            '(*foo *bar) OR (foo* bar*)',
            mangled_query)

    def test_substituted_value_never_contains_any_wildcards(self):
        # Simple term
        orig_query = '*f*oo*'
        pattern = '{value}'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals('foo', mangled_query)

        # Simple search
        orig_query = 'foo* *bar'
        pattern = '{value}'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals('(foo bar)', mangled_query)


class TestWildcardFunctions(TestCase):

    def test_searchterms_from_value_strips_wildcards(self):
        value = '*foo bar* b*az'
        terms = searchterms_from_value(value)
        self.assertEquals(['foo', 'bar', 'baz'], terms)

    # XXX: Output changed due changes in quote method from collective.solr.
    # The queryparser now recognizes boolean operators, therefore it's no
    # longer escaped.
    def test_searchterms_from_value_quotes_terms(self):
        value = 'foo&&bar'
        terms = searchterms_from_value(value)
        self.assertEquals(['foo&&bar'], terms)

    def test_searchterms_from_value_strips_parentheses(self):
        value = '(foo bar)'
        terms = searchterms_from_value(value)
        self.assertEquals(['foo', 'bar'], terms)

        value = ')foo bar('
        terms = searchterms_from_value(value)
        self.assertEquals(['foo', 'bar'], terms)

    def test_leading_wildcards_prepends_wildcards_to_all_terms(self):
        terms = 'foo bar qux'
        result = leading_wildcards(terms)
        self.assertEquals('(*foo *bar *qux)', result)

    def test_leading_wildcards_drops_existing_wildcards(self):
        terms = '*foo bar* qu*x'
        result = leading_wildcards(terms)
        self.assertEquals('(*foo *bar *qux)', result)

    def test_leading_wildcards_adds_parentheses(self):
        terms = 'foo bar'
        result = leading_wildcards(terms)
        self.assertTrue(result.startswith('('))
        self.assertTrue(result.endswith(')'))

    def test_trailing_wildcards_prepends_wildcards_to_all_terms(self):
        terms = 'foo bar qux'
        result = trailing_wildcards(terms)
        self.assertEquals('(foo* bar* qux*)', result)

    def test_trailing_wildcards_drops_existing_wildcards(self):
        terms = '*foo bar* qu*x'
        result = trailing_wildcards(terms)
        self.assertEquals('(foo* bar* qux*)', result)

    def test_trailing_wildcards_adds_parentheses(self):
        terms = 'foo bar'
        result = trailing_wildcards(terms)
        self.assertTrue(result.startswith('('))
        self.assertTrue(result.endswith(')'))


class TestQueryParameters(TestCase):

    def test_keep_valid_facet_fields(self):
        schema = SolrSchema()
        schema['foo'] = SolrField(indexed=True)
        schema['bar'] = SolrField(indexed=True)
        params = cleanupQueryParameters({'facet.field': 'foo'}, schema)
        self.assertEquals({'facet': 'true', 'facet.field': ['foo']}, params)
        params = cleanupQueryParameters({'facet.field': ['foo', 'bar']},
                                        schema)
        self.assertEquals({'facet': 'true', 'facet.field': ['foo', 'bar']},
                          params)

    def test_remove_invalid_facet_fields(self):
        schema = SolrSchema()
        params = cleanupQueryParameters({'facet.field': 'foo'}, schema)
        self.assertEquals({}, params)
        params = cleanupQueryParameters({'facet.field': ['foo', 'bar']},
                                        schema)
        self.assertEquals({}, params)

        schema['foo'] = SolrField(indexed=False)
        params = cleanupQueryParameters({'facet.field': 'foo'}, schema)
        self.assertEquals({}, params)
        params = cleanupQueryParameters({'facet.field': ['foo', 'bar']},
                                        schema)
        self.assertEquals({}, params)

    def test_remove_invalid_and_keep_valid_facet_fields(self):
        schema = SolrSchema()
        schema['bar'] = SolrField(indexed=True)
        params = cleanupQueryParameters({'facet.field': ['foo', 'bar']},
                                        schema)
        self.assertEquals({'facet': 'true', 'facet.field': ['bar']}, params)

    def test_insert_default_qt_parameter(self):
        self.assertEquals({'qt': 'select'}, subtractQueryParameters({}))

    def test_keep_existing_qt_parameter(self):
        self.assertEquals({'qt': 'search'}, subtractQueryParameters(
            {'qt': 'search'}))
