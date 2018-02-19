# -*- coding: utf-8 -*-
from ftw.solr.interfaces import ISolrSearch
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING
from mock import MagicMock
from plone import api
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility
import unittest


class TestSearch(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.solr = getUtility(ISolrSearch)
        self.solr._manager = MagicMock(name='SolrConnectionManager')
        self.conn = MagicMock(name='SolrConnection')
        self.solr.manager.connection = self.conn

    def test_security_filter_for_anonymous(self):
        logout()
        self.assertEqual(
            self.solr.security_filter(), u'allowedRolesAndUsers:Anonymous')

    def test_security_filter_for_authenticated_user(self):
        self.assertEqual(
            self.solr.security_filter(),
            u'allowedRolesAndUsers:(Member OR Authenticated OR Anonymous OR '
            u'user\:AuthenticatedUsers OR user\:test_user_1_)')

    def test_security_filter_contains_roles(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Member', 'Reader', 'Editor'])
        security_filter = self.solr.security_filter()
        self.assertIn(u'Member', security_filter)
        self.assertIn(u'Reader', security_filter)
        self.assertIn(u'Editor', security_filter)

    def test_security_filter_contains_groups(self):
        api.group.create(groupname='staff')
        api.group.add_user(groupname='staff', username=TEST_USER_ID)
        # Update groups in user object
        self.layer['portal'].acl_users._getGroupsForPrincipal(
            api.user.get_current().getUser())
        self.assertIn(u'user\\:staff', self.solr.security_filter())

    def test_security_filter_contains_current_user(self):
        self.assertIn(
            u'user\\:%s' % TEST_USER_ID,
            self.solr.security_filter())

    def test_security_filter_quotes_roles_and_users_with_spaces(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Records Manager', 'Member'])
        security_filter = self.solr.security_filter()
        self.assertIn('"Records Manager"', security_filter)

    def test_search_with_query(self):
        self.solr.search(query=u'Title:foo')
        args, kwargs = self.conn.search.call_args
        self.assertEqual(args[0][u'query'], u'Title:foo')

    def test_search_with_single_filter(self):
        self.solr.search(filters=u'portal_type:File')
        args, kwargs = self.conn.search.call_args
        self.assertEqual(
            args[0][u'filter'],
            [self.solr.security_filter(), u'portal_type:File'])

    def test_search_with_multiple_filters(self):
        self.solr.search(
            filters=[u'portal_type:File', u'review_state:published'])
        args, kwargs = self.conn.search.call_args
        self.assertEqual(
            args[0][u'filter'],
            [
                self.solr.security_filter(),
                u'portal_type:File',
                u'review_state:published',
            ])

    def test_search_with_pagination(self):
        self.solr.search(start=20, rows=10)
        args, kwargs = self.conn.search.call_args
        self.assertEqual(args[0][u'offset'], 20)
        self.assertEqual(args[0][u'limit'], 10)

    def test_search_with_sort(self):
        self.solr.search(sort='modified desc')
        args, kwargs = self.conn.search.call_args
        self.assertEqual(args[0][u'sort'], 'modified desc')

    def test_search_with_custom_parameters(self):
        self.solr.search(**{u'hl': u'on', u'hl.fl': u'SearchableText'})
        args, kwargs = self.conn.search.call_args
        self.assertEqual(
            args[0][u'params'],
            {u'hl': u'on', u'hl.fl': u'SearchableText'},
            )

    def test_search_with_custom_request_handler(self):
        self.solr.search(request_handler='/query')
        args, kwargs = self.conn.search.call_args
        self.assertEqual(kwargs, {'request_handler': u'/query'})
