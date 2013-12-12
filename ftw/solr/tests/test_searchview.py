# -*- coding: utf-8 -*-
from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from unittest2 import TestCase
from zope.component import getMultiAdapter
from zope.event import notify
from zope.traversing.interfaces import BeforeTraverseEvent
from collective.solr.flare import PloneFlare
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from ftw.solr.interfaces import ISearchSettings
from collective.solr.parser import SolrResponse


class TestSearchView(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_breadcrumbs(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        setRoles(portal, TEST_USER_ID, ['Manager'])
        f1 = portal[portal.invokeFactory('Folder', 'f1', title=u"Folder 1")]
        f2 = f1[f1.invokeFactory('Folder', 'f2', title=u"Folder 2")]
        f3 = f2[f2.invokeFactory('Folder', 'f3', title=u"Folder 3")]

        flare = PloneFlare(portal)
        flare['path_string'] = '/plone/f1/f2/f3'
        view = getMultiAdapter((f3, request), name=u'search')
        breadcrumbs = view.breadcrumbs(flare)
        self.assertEquals(len(breadcrumbs), 2)
        self.assertEquals(breadcrumbs[0]['Title'], 'Folder 1')
        self.assertEquals(breadcrumbs[0]['absolute_url'], f1.absolute_url())
        self.assertEquals(breadcrumbs[1]['Title'], 'Folder 2')
        self.assertEquals(breadcrumbs[1]['absolute_url'], f2.absolute_url())

    def test_path_based_breadcrumbs(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        # Enable path based breadcrumbs
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSettings)
        settings.path_based_breadcrumbs = True

        flare = PloneFlare(portal)
        flare['path_string'] = '/plone/path/to/object'
        view = getMultiAdapter((portal, request), name=u'search')
        breadcrumbs = view.breadcrumbs(flare)
        self.assertEquals(len(breadcrumbs), 2)
        self.assertEquals(breadcrumbs[0]['Title'], 'path')
        self.assertEquals(breadcrumbs[0]['absolute_url'],
            portal.absolute_url() + '/path')
        self.assertEquals(breadcrumbs[1]['Title'], 'to')
        self.assertEquals(breadcrumbs[1]['absolute_url'],
            portal.absolute_url() + '/path/to')

    def test_breadcrumbs_cropping(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        # Enable path based breadcrumbs
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSettings)
        settings.path_based_breadcrumbs = True

        flare = PloneFlare(portal)
        flare['path_string'] = '/plone/a/long/path/to/an/object'
        view = getMultiAdapter((portal, request), name=u'search')
        breadcrumbs = view.breadcrumbs(flare)
        self.assertEquals(len(breadcrumbs), 4)
        self.assertEquals(breadcrumbs[0]['Title'], 'a')
        self.assertEquals(breadcrumbs[1]['Title'], u'…')
        self.assertEquals(breadcrumbs[2]['Title'], 'to')
        self.assertEquals(breadcrumbs[3]['Title'], 'an')

        settings.max_breadcrumbs = 5
        breadcrumbs = view.breadcrumbs(flare)
        self.assertEquals(len(breadcrumbs), 5)
        self.assertEquals(breadcrumbs[0]['Title'], 'a')
        self.assertEquals(breadcrumbs[1]['Title'], 'long')
        self.assertEquals(breadcrumbs[2]['Title'], 'path')
        self.assertEquals(breadcrumbs[3]['Title'], 'to')
        self.assertEquals(breadcrumbs[4]['Title'], 'an')

    def test_calling_search_view(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        view = getMultiAdapter((portal, request), name=u'search')

        # Calling the @@search view without parameters shouldn't fail
        view()


    def test_filter_query_respecting_navroot(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSettings)
        view = getMultiAdapter((portal, request), name=u'search')

        # When respect_navroot is disabled...
        settings.respect_navroot = False

        query = view.filter_query({'SearchableText': 'ham'})
        self.assertEquals(query.get('path'), None,
            "No path filter should be added if there wasn't one already")

        request.form.update({'path': '/foo'})
        query = view.filter_query({'SearchableText': 'ham'})
        self.assertEquals(query.get('path'), '/foo',
            'Existing path filter should remain unchanged')

        # When respect_navroot is enabled...
        settings.respect_navroot = True

        del request.form['path']
        query = view.filter_query({'SearchableText': 'ham'})
        self.assertEquals(query.get('path'), '/plone',
            'Search should be constrained to navroot')

        request.form.update({'path': '/foo'})
        query = view.filter_query({'SearchableText': 'ham'})
        self.assertEquals(query.get('path'), '/foo',
            'Existing path filter should remain unchanged')


    def test_suggestions(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        request.form.update({'SearchableText': 'bidlung', })
        view = getMultiAdapter((portal, request), name=u'search')
        view.solr_response = SolrResponse()
        view.solr_response.spellcheck = {}
        view.solr_response.spellcheck['suggestions'] = {
            'bidlung': {'endOffset': 246,
                        'numFound': 5,
                        'origFreq': 1,
                        'startOffset': 239,
                        'suggestion': [{'freq': 2704, 'word': 'bildung'},
                                       {'freq': 1, 'word': 'bidlungs'},
                                       {'freq': 1, 'word': 'bidung'},
                                       {'freq': 561, 'word': 'bildungs'},
                                       {'freq': 233, 'word': 'bislang'}]},
            'platform': {'endOffset': 336,
                         'numFound': 5,
                         'origFreq': 9,
                         'startOffset': 328,
                         'suggestion': [{'freq': 557, 'word': 'plattform'},
                                        {'freq': 2, 'word': 'platforma'},
                                        {'freq': 2, 'word': 'platforme'},
                                        {'freq': 2, 'word': 'platforms'},
                                        {'freq': 7, 'word': 'plateforme'}]},
            'correctlySpelled': False,
        }

        suggestions = view.suggestions()
        self.assertEquals(suggestions[0][0], 'bildung')
        self.assertEquals(suggestions[0][1], '&SearchableText=bildung')


    def test_suggestions_querystring_with_list_parameter(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        request.form.update({'SearchableText': 'bidlung',
                             'facet.field': ['portal_type', 'review_state']})
        view = getMultiAdapter((portal, request), name=u'search')
        view.solr_response = SolrResponse()
        view.solr_response.spellcheck = {}
        view.solr_response.spellcheck['suggestions'] = {
            'bidlung': {'endOffset': 246,
                        'numFound': 5,
                        'origFreq': 1,
                        'startOffset': 239,
                        'suggestion': [{'freq': 2704, 'word': 'bildung'},
                                       {'freq': 1, 'word': 'bidlungs'},
                                       {'freq': 1, 'word': 'bidung'},
                                       {'freq': 561, 'word': 'bildungs'},
                                       {'freq': 233, 'word': 'bislang'}]},
            'correctlySpelled': False,
        }

        suggestions = view.suggestions()
        self.assertEquals('bildung', suggestions[0][0])
        self.assertIn('&facet.field=portal_type&facet.field=review_state',
                      suggestions[0][1])
        self.assertIn('&SearchableText=bildung', suggestions[0][1])