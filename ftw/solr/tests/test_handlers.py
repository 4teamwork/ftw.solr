# -*- coding: utf-8 -*-
from DateTime import DateTime
from ftw.solr.connection import SolrResponse
from ftw.solr.handlers import ATBlobFileIndexHandler
from ftw.solr.handlers import DefaultIndexHandler
from ftw.solr.handlers import DexterityItemIndexHandler
from ftw.solr.schema import SolrSchema
from ftw.solr.testing import FTW_SOLR_AT_INTEGRATION_TESTING
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING
from ftw.solr.tests.utils import get_data
from ftw.solr.tests.utils import normalize_whitespaces
from mock import MagicMock
from mock import PropertyMock
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.namedfile.file import NamedBlobFile
from plone.uuid.interfaces import IMutableUUID
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import getFSVersionTuple
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
        data = self.handler.get_data(None)
        data['SearchableText'] = normalize_whitespaces(data['SearchableText'])
        self.assertEqual(
            {
                u'Title': u'My Document',
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
                u'allowedRolesAndUsers': [u'Anonymous'],
                u'path': u'/plone/doc',
                u'path_depth': 2,
                u'modified': u'2017-01-21T17:18:19.000Z',
                u'SearchableText': 'doc My Document',
            },
            data
        )

    def test_get_data_gets_only_specified_attributes(self):
        self.assertEqual(
            {
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
                u'modified': u'2017-01-21T17:18:19.000Z',
            },
            self.handler.get_data(['UID', 'modified'])
        )

    def test_get_data_always_includes_unique_key(self):
        self.assertEqual(
            {
                u'Title': u'My Document',
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            },
            self.handler.get_data(['Title'])
        )

    def test_get_data_includes_path_depth_if_exists_and_path_was_included(self):
        self.assertEqual(
            {
                u'path': u'/plone/doc',
                u'path_depth': 2,
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            },
            self.handler.get_data(['path'])
        )

        # solr schemas without the path_depth field
        self.manager.schema.fields.pop('path_depth')
        self.assertEqual(
            {
                u'path': u'/plone/doc',
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            },
            self.handler.get_data(['path'])
        )

    def test_add_without_attributes_adds_full_documemt(self):
        self.manager.connection.add = MagicMock(name='add')
        self.handler.add(None)
        data = self.manager.connection.add.call_args[0][0]
        data['SearchableText'] = normalize_whitespaces(data['SearchableText'])
        self.assertEqual(
            {
                u'UID': u'09baa75b67f44383880a6dab8b3200b6',
                u'Title': u'My Document',
                u'modified': u'2017-01-21T17:18:19.000Z',
                u'SearchableText': 'doc My Document',
                u'allowedRolesAndUsers': [u'Anonymous'],
                u'path': u'/plone/doc',
                u'path_depth': 2,
            },
            data
        )

    def test_add_with_attributes_does_atomic_update(self):
        self.manager.connection.add = MagicMock(name='add')
        self.handler.add(['Title', 'modified'])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': {'set': u'My Document'},
            u'modified': {'set': u'2017-01-21T17:18:19.000Z'},
        })

    def test_add_with_attributes_without_data_does_nothing(self):
        self.manager.connection.add = MagicMock(name='add')
        self.handler.add(['field_not_in_schema'])
        self.assertFalse(self.manager.connection.add.called)

    def test_delete(self):
        self.manager.connection.delete = MagicMock(name='delete')
        self.handler.delete()
        self.manager.connection.delete.assert_called_once_with(
            u'09baa75b67f44383880a6dab8b3200b6')


@unittest.skipIf(getFSVersionTuple() >= (5, 0),
                 'Files are not AT-based on Plone 5 and later')
class TestATBlobFileIndexHandler(unittest.TestCase):

    layer = FTW_SOLR_AT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.doc = api.content.create(
            type='File', title='My File', id='doc',
            file='File data ...', container=self.portal)

        field = self.doc.getPrimaryField().get(self.doc)
        field.setFilename('document.docx')
        field.setContentType('application/vnd.openxmlformats-officedocument.wordprocessingml.document')

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
        self.handler = ATBlobFileIndexHandler(self.doc, self.manager)

    def test_add_without_attributes_calls_add_and_extract(self):
        self.manager.connection.add = MagicMock(name='add')
        self.manager.connection.extract = MagicMock(name='extract')
        self.handler.add(None)
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': {u'set': u'My File'},
            u'modified': {u'set': u'2017-01-21T17:18:19.000Z'},
            u'allowedRolesAndUsers': {u'set': [u'Anonymous']},
            u'path': {u'set': u'/plone/doc'},
            u'path_depth': {u'set': 2},
        })
        self.manager.connection.extract.assert_called_once_with(
            self.doc.getFile().blob,
            'SearchableText',
            {u'UID': u'09baa75b67f44383880a6dab8b3200b6'},
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_add_with_attributes_without_searchabletext_calls_add(self):
        self.manager.connection.add = MagicMock(name='add')
        self.manager.connection.extract = MagicMock(name='extract')
        self.handler.add(['Title', 'modified'])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': {'set': u'My File'},
            u'modified': {'set': u'2017-01-21T17:18:19.000Z'},
        })
        self.manager.connection.extract.assert_not_called()

    def test_add_with_attributes_with_searchabletext_calls_add_and_extract(self):
        self.manager.connection.add = MagicMock(name='add')
        self.manager.connection.extract = MagicMock(name='extract')
        self.handler.add(['SearchableText', 'modified'])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'modified': {'set': u'2017-01-21T17:18:19.000Z'},
        })
        self.manager.connection.extract.assert_called_once_with(
            self.doc.getFile().blob,
            'SearchableText',
            {u'UID': u'09baa75b67f44383880a6dab8b3200b6'},
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_add_with_searchabletext_only_calls_extract(self):
        self.manager.connection.add = MagicMock(name='add')
        self.manager.connection.extract = MagicMock(name='extract')
        self.handler.add(['SearchableText'])
        self.manager.connection.add.assert_not_called()
        self.manager.connection.extract.assert_called_once_with(
            self.doc.getFile().blob,
            'SearchableText',
            {u'UID': u'09baa75b67f44383880a6dab8b3200b6'},
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_add_with_attributes_without_data_does_nothing(self):
        self.manager.connection.add = MagicMock(name='add')
        self.handler.add(['field_not_in_schema'])
        self.assertFalse(self.manager.connection.add.called)


class TestDexterityItemIndexHandler(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        namedfile = NamedBlobFile(
            data='File data ...',
            filename=u'document.docx',
            contentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.doc = api.content.create(
            type='File', title='My File', id='doc',
            file=namedfile, container=self.portal)
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
        self.handler = DexterityItemIndexHandler(self.doc, self.manager)

        self.manager.connection.add = MagicMock(name='add')
        self.manager.connection.extract = MagicMock(name='extract')

    def test_add_without_attributes_calls_add_and_extract(self):
        self.handler.add(None)
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': {u'set': u'My File'},
            u'modified': {u'set': u'2017-01-21T17:18:19.000Z'},
            u'allowedRolesAndUsers': {u'set': [u'Anonymous']},
            u'path': {u'set': u'/plone/doc'},
            u'path_depth': {u'set': 2},
        })
        self.manager.connection.extract.assert_called_once_with(
            self.doc.file._blob,
            'SearchableText',
            {u'UID': u'09baa75b67f44383880a6dab8b3200b6'},
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_add_with_empty_list_attributes_calls_add_and_extract(self):
        self.handler.add([])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': {u'set': u'My File'},
            u'modified': {u'set': u'2017-01-21T17:18:19.000Z'},
            u'allowedRolesAndUsers': {u'set': [u'Anonymous']},
            u'path': {u'set': u'/plone/doc'},
            u'path_depth': {u'set': 2},
        })
        self.manager.connection.extract.assert_called_once_with(
            self.doc.file._blob,
            'SearchableText',
            {u'UID': u'09baa75b67f44383880a6dab8b3200b6'},
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_add_with_attributes_without_searchabletext_calls_add(self):
        self.handler.add(['Title', 'modified'])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'Title': {'set': u'My File'},
            u'modified': {'set': u'2017-01-21T17:18:19.000Z'},
        })
        self.manager.connection.extract.assert_not_called()

    def test_add_with_attributes_with_searchabletext_calls_add_and_extract(self):
        self.handler.add(['SearchableText', 'modified'])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'09baa75b67f44383880a6dab8b3200b6',
            u'modified': {'set': u'2017-01-21T17:18:19.000Z'},
        })
        self.manager.connection.extract.assert_called_once_with(
            self.doc.file._blob,
            'SearchableText',
            {u'UID': u'09baa75b67f44383880a6dab8b3200b6'},
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_add_with_searchabletext_only_calls_extract(self):
        self.handler.add(['SearchableText'])
        self.manager.connection.add.assert_not_called()
        self.manager.connection.extract.assert_called_once_with(
            self.doc.file._blob,
            'SearchableText',
            {u'UID': u'09baa75b67f44383880a6dab8b3200b6'},
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    def test_add_without_attributes_for_item_without_blob_calls_add(self):
        item = api.content.create(
            type='Document', title='My Document', id='doc2',
            container=self.portal)
        IMutableUUID(item).set('56d2c8b62c064f38890c60b66d01c894')
        item.modification_date = DateTime('2017-01-21T17:18:19+00:00')

        handler = DexterityItemIndexHandler(item, self.manager)
        handler.add(None)
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'56d2c8b62c064f38890c60b66d01c894',
            u'Title': {u'set': u'My Document'},
            u'modified': {u'set': u'2017-01-21T17:18:19.000Z'},
            u'SearchableText': {'set': ' doc2 My Document   '},
            u'allowedRolesAndUsers': {u'set': [u'Anonymous']},
            u'path': {u'set': u'/plone/doc2'},
            u'path_depth': {u'set': 2},
        })
        self.manager.connection.extract.assert_not_called()

    def test_add_with_attributes_for_item_without_blob_calls_add(self):
        item = api.content.create(
            type='Document', title='My Document', id='doc2',
            container=self.portal)
        IMutableUUID(item).set('56d2c8b62c064f38890c60b66d01c894')
        item.modification_date = DateTime('2017-01-21T17:18:19+00:00')

        handler = DexterityItemIndexHandler(item, self.manager)
        handler.add(['SearchableText', 'modified'])
        self.manager.connection.add.assert_called_once_with({
            u'UID': u'56d2c8b62c064f38890c60b66d01c894',
            u'modified': {u'set': u'2017-01-21T17:18:19.000Z'},
            u'SearchableText': {'set': ' doc2 My Document   '},
        })
        self.manager.connection.extract.assert_not_called()

    def test_add_with_attributes_without_data_does_nothing(self):
        self.manager.connection.add = MagicMock(name='add')
        self.handler.add(['field_not_in_schema'])
        self.assertFalse(self.manager.connection.add.called)
