from unittest import TestCase
from ftw.solr.patches.mangler import cleanupQueryParameters
from ftw.solr.patches.mangler import extractQueryParameters
from collective.solr.parser import SolrSchema, SolrField
from ftw.solr.patches.mangler import mangleQuery
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.manager import SolrConnectionConfig
from collective.solr.tests.utils import getData
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
