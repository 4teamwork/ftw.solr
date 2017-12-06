from ftw.solr.connection import SolrConnectionManager
from ftw.solr.schema import SolrSchema
from ftw.solr.tests.utils import get_data
from ftw.solr.tests.utils import MockHTTPResponse
from mock import patch
import unittest


class TestSchema(unittest.TestCase):

    def test_api_path_for_single_core(self):
        schema = SolrSchema(core='mycore')
        self.assertEqual(schema.api_path, '/api/cores/mycore/schema')

    def test_api_path_for_solrcloud(self):
        schema = SolrSchema(collection='mycollection')
        self.assertEqual(schema.api_path, '/api/c/mycollection/schema')

    @patch('ftw.solr.connection.HTTPConnection', autospec=True)
    def test_schema_retrieval(self, MockHTTPConnection):
        MockHTTPConnection.return_value.request.return_value = None
        MockHTTPConnection.return_value.getresponse.return_value = MockHTTPResponse(body=get_data('schema.json'))
        manager = SolrConnectionManager()
        schema = SolrSchema(core='mycore')
        schema._manager = manager
        schema.retrieve()
        self.assertEqual(schema.version, 1.6)
        self.assertEqual(schema.unique_key, 'UID')
        self.assertEqual(
            schema.fields.keys(), [u'_version_', u'_root_', u'UID'])
        self.assertEqual(schema.copy_fields.keys(), [])
        self.assertEqual(schema.dynamic_fields.keys(), [])
        self.assertEqual(
            schema.field_types.keys(), [u'boolean', u'string', u'plong'])
