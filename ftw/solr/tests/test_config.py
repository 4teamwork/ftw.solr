from ftw.solr.config import SolrConfig
from ftw.solr.connection import SolrResponse
from ftw.solr.tests.utils import get_data
from mock import MagicMock
from mock import PropertyMock
import unittest


class TestConfig(unittest.TestCase):

    def setUp(self):
        conn = MagicMock(name='SolrConnection')
        conn.get = MagicMock(name='get', return_value=SolrResponse(
            body=get_data('config_langid.json'), status=200))
        manager = MagicMock(name='SolrConnectionManager')
        type(manager).connection = PropertyMock(return_value=conn)
        self.config = SolrConfig(manager)

    def test_config_retrieval(self):
        config = self.config
        self.assertEqual(config.config[u'luceneMatchVersion'], u'8.11.1')

    def test_langid_settings(self):
        self.assertEqual(
            self.config.langid_fields,
            [u'Description', u'SearchableText', u'Title'],
        )
        self.assertEqual(
            self.config.langid_langs, [u'de', u'en', u'fr', u'general'])
        self.assertEqual(
            self.config.langid_langfields,
            [
                u'Description_de',
                u'Description_en',
                u'Description_fr',
                u'Description_general',
                u'SearchableText_de',
                u'SearchableText_en',
                u'SearchableText_fr',
                u'SearchableText_general',
                u'Title_de',
                u'Title_en',
                u'Title_fr',
                u'Title_general',
            ],
        )

    def test_langid_settings_without_langid_processor(self):
        conn = MagicMock(name='SolrConnection')
        conn.get = MagicMock(name='get', return_value=SolrResponse(
            body=get_data('config.json'), status=200))
        manager = MagicMock(name='SolrConnectionManager')
        type(manager).connection = PropertyMock(return_value=conn)
        config = SolrConfig(manager)
        self.assertEqual(config.langid_fields, [])
        self.assertEqual(config.langid_langs, [])
        self.assertEqual(config.langid_langfields, [])
