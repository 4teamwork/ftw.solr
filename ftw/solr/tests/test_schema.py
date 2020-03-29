from ftw.solr.connection import SolrResponse
from ftw.solr.schema import SolrSchema
from ftw.solr.tests.utils import get_data
from mock import MagicMock
from mock import PropertyMock

import six
import unittest


class TestSchema(unittest.TestCase):

    def setUp(self):
        conn = MagicMock(name='SolrConnection')
        conn.get = MagicMock(name='get', return_value=SolrResponse(
            body=get_data('schema.json'), status=200))
        manager = MagicMock(name='SolrConnectionManager')
        type(manager).connection = PropertyMock(return_value=conn)
        self.schema = SolrSchema(manager)

    def test_schema_retrieval(self):
        schema = self.schema
        self.assertEqual(schema.version, 1.6)
        self.assertEqual(schema.unique_key, 'UID')
        six.assertCountEqual(
            self,
            list(schema.fields),
            [
                u'Title',
                u'modified',
                u'SearchableText',
                u'allowedRolesAndUsers',
                u'_version_',
                u'_root_',
                u'UID',
                u'path',
                u'path_depth',
            ])
        self.assertEqual(list(schema.copy_fields), [])
        self.assertEqual(list(schema.dynamic_fields), [])
        six.assertCountEqual(
            self,
            list(schema.field_types),
            [
                u'boolean',
                u'string',
                u'plong',
                u'pint',
                u'text',
                u'pdate',
            ])

    def test_get_field_class_of_existing_field(self):
        self.assertEqual(self.schema.field_class('UID'), 'solr.StrField')

    def test_get_field_class_of_not_existing_field(self):
        self.assertEqual(self.schema.field_class('foo'), None)
