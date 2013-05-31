# -*- coding: utf-8 -*-
from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from unittest2 import TestCase
from zope.component import getMultiAdapter, queryUtility
from zope.event import notify
from zope.traversing.interfaces import BeforeTraverseEvent
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.tests.utils import fakehttp
from ftw.solr.tests.utils import getData
import json


class TestSuggestView(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_suggest(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        # Setup solr suggest response
        response = getData('suggest_response.txt')
        proc = queryUtility(ISolrConnectionManager)
        proc.setHost(active=True)
        conn = proc.getConnection()
        fakehttp(conn, response)

        request.form.update({'term': 'ab'})
        view = getMultiAdapter((portal, request), name=u'suggest-terms')
        suggestions = json.loads(view())

        self.assertEquals(len(suggestions), 9)
        self.assertEquals(suggestions[0]['value'], 'aber')
        self.assertEquals(suggestions[0]['label'], 'aber')

    def test_no_suggest(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        # Setup solr suggest response
        response = getData('nosuggest_response.txt')
        proc = queryUtility(ISolrConnectionManager)
        proc.setHost(active=True)
        conn = proc.getConnection()
        fakehttp(conn, response)

        request.form.update({'term': 'abx'})
        view = getMultiAdapter((portal, request), name=u'suggest-terms')
        suggestions = json.loads(view())
        self.assertEquals(len(suggestions), 0)
