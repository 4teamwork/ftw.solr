# -*- coding: utf-8 -*-
from DateTime import DateTime
from ftw.solr.connection import SolrResponse
from ftw.solr.handlers import DefaultIndexHandler
from ftw.solr.schema import SolrSchema
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING
from ftw.solr.tests.utils import get_data
from mock import MagicMock
from mock import PropertyMock
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IMutableUUID
from Products.CMFPlone.utils import base_hasattr
import unittest


class TestDefaultIndexHandler(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.doc = api.content.create(
            type='Document', title='My Document', id='doc',
            container=self.portal)
        if base_hasattr(self.doc, '_setUID'):
            self.doc._setUID('09baa75b67f44383880a6dab8b3200b6')
            self.doc.setModificationDate(DateTime('2017-01-21T17:18:19+00:00'))
        else:
            IMutableUUID(self.doc).set('09baa75b67f44383880a6dab8b3200b6')
            self.doc.modification_date = DateTime('2017-01-21T17:18:19+00:00')

        conn = MagicMock(name='SolrConnection')
        conn.get = MagicMock(name='get', return_value=SolrResponse(
            body=get_data('schema.json'), status=200))
        self.manager = MagicMock(name='SolrConnectionManager')
        type(self.manager).connection = PropertyMock(return_value=conn)
        type(self.manager).schema = PropertyMock(return_value=SolrSchema(
            self.manager))
        self.handler = DefaultIndexHandler(self.doc, self.manager)

    def test_get_data_without_attributes_gets_all_fields(self):
        self.assertEqual(
            {
                u'Title': u'My Document',
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
                u'allowedRolesAndUsers': [u'Anonymous'],
                u'path': u'/plone/doc',
                u'modified': u'2017-01-21T17:18:19.000Z',
                u'SearchableText': 'doc  My Document ',
            },
            self.handler.get_data(None)
        )

    def test_get_data_gets_only_specified_attributes(self):
        self.assertEqual(
            {
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
                u'path': u'/plone/doc',
            },
            self.handler.get_data(['UID', 'path'])
        )

    def test_get_data_always_includes_unique_key(self):
        self.assertEqual(
            {
                u'Title': u'My Document',
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            },
            self.handler.get_data(['Title'])
        )

    def test_add_without_attributes_adds_full_documemt(self):
        self.manager.connection.add = MagicMock(name='add')
        self.handler.add(None)
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': u'My Document',
            u'modified': u'2017-01-21T17:18:19.000Z',
            u'SearchableText': 'doc  My Document ',
            u'allowedRolesAndUsers': [u'Anonymous'],
            u'path': u'/plone/doc',
        })

    def test_add_with_attributes_does_atomic_update(self):
        self.manager.connection.add = MagicMock(name='add')
        self.handler.add(['Title', 'path'])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': {'set': u'My Document'},
            u'path': {'set': u'/plone/doc'},
        })

    def test_delete(self):
        self.manager.connection.delete = MagicMock(name='delete')
        self.handler.delete()
        self.manager.connection.delete.assert_called_once_with(
            u'09baa75b67f44383880a6dab8b3200b6')
