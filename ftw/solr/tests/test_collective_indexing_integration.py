# -*- coding: utf-8 -*-
from collective.indexing.queue import getQueue
from datetime import datetime
from ftw.solr.connection import SolrResponse
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexQueueProcessor
from ftw.solr.schema import SolrSchema
from ftw.solr.testing import FTW_SOLR_COLLECTIVE_INDEXING_INTEGRATION_TESTING
from ftw.solr.tests.utils import get_data
from ftw.testing import freeze
from mock import call
from mock import MagicMock
from mock import PropertyMock
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IUUID
from zope.component import getUtility
from zope.interface import alsoProvides
import unittest


class TestCollectiveIndexingIntegration(unittest.TestCase):

    layer = FTW_SOLR_COLLECTIVE_INDEXING_INTEGRATION_TESTING

    def setUp(self):
        super(TestCollectiveIndexingIntegration, self).setUp()
        self.portal = self.layer['portal']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        # Prepare nested folders so 'View' isn't mapped to the 'Reader' role.
        # First subtree has a leaf node folder with 'View' acquired, whereas
        # the second subtree has a leaf node folder with AQ disabled for 'View'
        self.folder = api.content.create(
            type='Folder', title='My Folder',
            id='folder', container=self.portal)
        self.folder.manage_permission('View', roles=['Other'], acquire=False)

        self.subfolder = api.content.create(
            type='Folder', title='My Subfolder',
            id='subfolder', container=self.folder)
        self.subfolder.manage_permission('View', roles=['Other'], acquire=True)

        self.folder2 = api.content.create(
            type='Folder', title='My Folder 2',
            id='folder2', container=self.portal)
        self.folder2.manage_permission('View', roles=['Other'], acquire=False)

        self.subfolder2_without_aq = api.content.create(
            type='Folder', title='My Subfolder without acquired permission',
            id='subfolder2_without_aq', container=self.folder2)
        self.subfolder2_without_aq.manage_permission('View', roles=['Other'], acquire=False)

        self.folder.reindexObjectSecurity()
        self.folder2.reindexObjectSecurity()
        self.subfolder.reindexObjectSecurity()
        self.subfolder2_without_aq.reindexObjectSecurity()

        # Flush queue to avoid having the above objects getting indexed at
        # the end of the transaction, after we already installed the mocks
        getQueue().process()

        self.manager = MagicMock(name='SolrConnectionManager')
        alsoProvides(self.manager, ISolrConnectionManager)

        conn = MagicMock(name='SolrConnection')
        conn.get = MagicMock(name='get', return_value=SolrResponse(
            body=get_data('schema.json'), status=200))
        type(self.manager).connection = PropertyMock(return_value=conn)
        type(self.manager).schema = PropertyMock(
            return_value=SolrSchema(self.manager))

        sm = self.portal.getSiteManager()
        sm.registerUtility(self.manager, ISolrConnectionManager)

        self.connection = self.manager.connection

        # Manager is memoized on the ISolrIndexQueueProcessor - reset it
        queue_processor = getUtility(ISolrIndexQueueProcessor, name='ftw.solr')
        queue_processor._manager = None

    def test_reindex_object_causes_full_reindex_in_solr(self):
        with freeze(datetime(2018, 8, 31, 13, 45)):
            self.subfolder.reindexObject()
        getQueue().process()

        self.connection.add.assert_called_once_with({
            u'UID': IUUID(self.subfolder),
            u'Title': u'My Subfolder',
            u'modified': u'2018-08-31T11:45:00.000Z',
            u'SearchableText': 'subfolder  My Subfolder ',
            u'allowedRolesAndUsers': ['Other'],
            u'path': u'/plone/folder/subfolder',
        })

    def test_reindex_object_with_idxs_causes_atomic_update(self):
        self.subfolder.reindexObject(idxs=['Title'])
        getQueue().process()

        self.connection.add.assert_called_once_with({
            u'UID': IUUID(self.subfolder),
            u'Title': {'set': u'My Subfolder'},
        })

    def test_reindex_object_security_causes_atomic_update(self):
        # Subfolder previously hasn't had 'View' mapped to any roles.
        # Explicitly give it to 'Reader' role.
        self.subfolder.manage_permission(
            'View', roles=['Reader'], acquire=False)

        self.subfolder.reindexObjectSecurity()
        getQueue().process()

        self.connection.add.assert_called_once_with({
            u'UID': IUUID(self.subfolder),
            u'allowedRolesAndUsers': {'set': [u'Reader']},
        })

    def test_reindex_object_security_is_recursive(self):
        # Both folder and subfolder haven't previously had 'View' mapped to
        # any roles. Subfolder has 'View' set to acquire though. Giving it
        # to 'Reader' on Folder should therefore propagate down to Subfolder.
        self.folder.manage_permission('View', roles=['Reader'], acquire=False)

        self.folder.reindexObjectSecurity()
        getQueue().process()

        expected_calls = [
            call({
                'allowedRolesAndUsers': {'set': [u'Reader']},
                u'UID': IUUID(self.folder)}),
            call({
                'allowedRolesAndUsers': {'set': [u'Other', u'Reader']},
                u'UID': IUUID(self.subfolder)})
        ]
        self.assertEqual(2, len(self.connection.add.mock_calls))
        # XXX: Why isn't call order stable here?
        self.connection.add.assert_has_calls(expected_calls, any_order=True)

    def test_reindex_object_security_honors_skip_self(self):
        self.subfolder.manage_permission('View', roles=['Reader'], acquire=False)

        self.subfolder.reindexObjectSecurity(skip_self=True)
        getQueue().process()

        self.assertEqual(0, len(self.connection.add.mock_calls))

    def test_reindex_object_security_stops_recursion_early_if_possible(self):
        # Both folder2 and subfolder_without_aq haven't previously had 'View'
        # mapped to any roles. subfolder_without_aq has Acquisition diabled
        # for 'View', and should therefore be skipped during reindex because
        # it's effective security index contents don't change.
        self.folder2.manage_permission('View', roles=['Reader'], acquire=False)

        self.folder2.reindexObjectSecurity()
        getQueue().process()

        self.connection.add.assert_called_once_with({
            u'allowedRolesAndUsers': {'set': [u'Reader']},
            u'UID': IUUID(self.folder2)})
