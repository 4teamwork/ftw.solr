from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.manager import SolrConnectionConfig
from collective.solr.parser import SolrSchema, SolrField
from collective.solr.tests.utils import getData
from ftw.solr.patches.mangler import cleanupQueryParameters
from ftw.solr.patches.mangler import extractQueryParameters
from ftw.solr.patches.mangler import mangleQuery
from ftw.solr.patches.mangler import mangle_searchable_text_query
from unittest import TestCase
from zope.component import provideUtility, getUtility


class TestQueryMangler(TestCase):

    def setUp(self):
        provideUtility(SolrConnectionConfig(), ISolrConnectionConfig)
        xml = getData('plone_schema.xml')
        xml = xml[xml.find('<schema'):]
        self.schema = SolrSchema(xml.strip())

    def test_search_pattern_base_value_is_lowercase(self):
        config = getUtility(ISolrConnectionConfig)
        config.search_pattern = '{value} OR searchwords:{base_value}^1000'

        query = dict(SearchableText='Pass')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['(pass* OR pass) OR searchwords:pass^1000'])},
            query
        )

        query = dict(SearchableText='Pass*')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['pass* OR searchwords:pass^1000'])},
            query
        )

        query = dict(SearchableText='Pass port')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['(pass port) OR searchwords:pass port^1000'])},
            query
        )

    def test_simple_terms_result_in_value_with_appended_wildcard(self):
        config = getUtility(ISolrConnectionConfig)
        config.search_pattern = '{value}'

        query = dict(SearchableText='foo')
        mangleQuery(query, config, self.schema)
        self.assertEquals(
            {'SearchableText': set(['(foo* OR foo)'])},
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


class TestMangleSearchableTextQuery(TestCase):

    def test_simple_terms_result_in_basic_wildcard_search(self):
        orig_query = 'foo'
        pattern = '{value} OR searchwords:{base_value}^1000'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals(
            '(foo* OR foo) OR searchwords:foo^1000',
            mangled_query)

    def test_simple_search_results_in_simple_pattern_substitution(self):
        orig_query = 'foo bar'
        pattern = '{value} OR searchwords:{base_value}^1000'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals(
            '(foo bar) OR searchwords:foo bar^1000',
            mangled_query)

    def test_simple_search_drops_wildcards_for_base_value_and_quotes_it(self):
        orig_query = 'foo* bar*'
        pattern = '{value} OR searchwords:{base_value}^1000'
        mangled_query = mangle_searchable_text_query(orig_query, pattern)
        self.assertEquals(
            '(foo* bar*) OR searchwords:(foo bar)^1000',
            mangled_query)


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
        self.assertEquals({'qt': 'select'}, extractQueryParameters({}))

    def test_keep_existing_qt_parameter(self):
        self.assertEquals({'qt': 'search'}, extractQueryParameters(
            {'qt': 'search'}))
