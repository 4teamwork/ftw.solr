from unittest import TestCase
from ftw.solr.patches.mangler import cleanupQueryParameters
from ftw.solr.patches.mangler import extractQueryParameters
from collective.solr.parser import SolrSchema, SolrField


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
