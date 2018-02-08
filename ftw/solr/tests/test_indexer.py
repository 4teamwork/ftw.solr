# -*- coding: utf-8 -*-
from ftw.solr.indexer import SolrIndexQueueProcessor
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexHandler
from mock import MagicMock
from mock import PropertyMock
from plone.testing import zca
from zope.component import provideAdapter
from zope.component import provideUtility
from zope.interface import Interface
import unittest


class MockSolrIndexHandler(object):

    add = MagicMock(name='add')
    delete = MagicMock(name='delete')

    def __init__(self, context, manager):
        self.manger = manager


class TestSolrIndexQueueProcessor(unittest.TestCase):

    layer = zca.UNIT_TESTING

    def setUp(self):
        self.indexer = SolrIndexQueueProcessor()
        self.indexer._manager = MagicMock(name='SolrConnectionManager')
        provideAdapter(
            MockSolrIndexHandler,
            adapts=(Interface, MagicMock),
            provides=ISolrIndexHandler,
        )
        conn = MagicMock(name='SolrConnection')
        conn.commit = MagicMock(name='commit')
        type(self.indexer._manager).connection = PropertyMock(
            return_value=conn)

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
