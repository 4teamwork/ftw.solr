# -*- coding: utf-8 -*-
from ftw.solr.indexer import SolrIndexQueueProcessor
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexHandler
from ftw.solr.interfaces import ISolrSettings
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING
from mock import MagicMock
from mock import PropertyMock
from plone.app.testing import popGlobalRegistry
from plone.app.testing import pushGlobalRegistry
from plone.registry.interfaces import IRegistry
from zope.component import provideAdapter
from zope.component import provideUtility
from zope.component import queryUtility
from zope.interface import Interface
import unittest


class MockSolrIndexHandler(object):

    add = MagicMock(name='add')
    delete = MagicMock(name='delete')

    def __init__(self, context, manager):
        self.manger = manager


class TestSolrIndexQueueProcessor(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.indexer = SolrIndexQueueProcessor()
        self.indexer._manager = MagicMock(name='SolrConnectionManager')
        pushGlobalRegistry(self.layer['portal'])
        provideAdapter(
            MockSolrIndexHandler,
            adapts=(Interface, MagicMock),
            provides=ISolrIndexHandler,
        )
        conn = MagicMock(name='SolrConnection')
        conn.commit = MagicMock(name='commit')
        type(self.indexer._manager).connection = PropertyMock(
            return_value=conn)

    def tearDown(self):
        popGlobalRegistry(self.layer['portal'])

    def disable_indexing(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(ISolrSettings)
        settings.enabled = False

    def test_index_object_without_providing_attributes_calls_add(self):
        self.indexer.index(object())
        MockSolrIndexHandler.add.assert_called_with(None)

    def test_index_object_with_provided_attributes_calls_add(self):
        self.indexer.index(object(), attributes=['path'])
        MockSolrIndexHandler.add.assert_called_with(['path'])

    def test_reindex_object_without_providing_attributes_calls_add(self):
        self.indexer.reindex(object())
        MockSolrIndexHandler.add.assert_called_with(None)

    def test_reindex_object_with_provided_attributes_calls_add(self):
        self.indexer.reindex(object(), attributes=['path', 'Title'])
        MockSolrIndexHandler.add.assert_called_with(['path', 'Title'])

    def test_unindex_object_calls_delete(self):
        self.indexer.unindex(object())
        MockSolrIndexHandler.delete.assert_called_with()

    def test_begin_does_nothing(self):
        self.indexer.manager.connection.commit.assert_not_called()
        self.indexer.manager.connection.abort.assert_not_called()

    def test_commit_calls_connection_commit(self):
        self.indexer.commit()
        self.indexer.manager.connection.commit.assert_called_with()

    def test_abort_calls_connection_abort(self):
        self.indexer.abort()
        self.indexer.manager.connection.abort.assert_called_with()

    def test_manager_returns_registered_utility(self):
        self.indexer._manager = None
        util = object()
        provideUtility(util, ISolrConnectionManager)
        self.assertEqual(util, self.indexer.manager)

    def test_index_does_not_call_add_if_disabled(self):
        self.disable_indexing()
        self.indexer.index(object())
        self.assertFalse(
            MockSolrIndexHandler.add.called, 'Should not call add')

    def test_unindex_does_not_call_delete_if_disabled(self):
        self.disable_indexing()
        self.indexer.unindex(object())
        self.assertFalse(
            MockSolrIndexHandler.delete.called, 'Should not call delete')

    def test_commit_does_not_call_commit_if_disabled(self):
        self.disable_indexing()
        self.indexer.commit()
        self.assertFalse(
            self.indexer.manager.connection.commit.called,
            'Should not call commit')

    def test_abort_does_not_call_abort_if_disabled(self):
        self.disable_indexing()
        self.indexer.abort()
        self.assertFalse(
            self.indexer.manager.connection.abort.called,
            'Should not call abort')
