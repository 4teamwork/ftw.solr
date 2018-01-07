from ftw.solr.connection import SolrResponse
from ftw.solr.schema import SolrSchema
from ftw.solr.tests.utils import get_data
from mock import MagicMock
from mock import PropertyMock
import unittest


class TestSchema(unittest.TestCase):

    def test_schema_retrieval(self):
        conn = MagicMock(name='SolrConnection')
        conn.get = MagicMock(name='get', return_value=SolrResponse(
            body=get_data('schema.json'), status=200))
        manager = MagicMock(name='SolrConnectionManager')
        type(manager).connection = PropertyMock(return_value=conn)
        schema = SolrSchema(manager)
        schema.retrieve()
        self.assertEqual(schema.version, 1.6)
        self.assertEqual(schema.unique_key, 'UID')
        self.assertItemsEqual(
            schema.fields.keys(),
            [
                u'Title',
                u'modified',
                u'SearchableText',
                u'allowedRolesAndUsers',
                u'_version_',
                u'_root_',
                u'UID',
                u'path',
            ])
        self.assertEqual(schema.copy_fields.keys(), [])
        self.assertEqual(schema.dynamic_fields.keys(), [])
        self.assertItemsEqual(
            schema.field_types.keys(),
            [
                u'boolean',
                u'string',
                u'plong',
                u'text',
                u'pdate',
            ])
