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
from plone.app.contentlisting.interfaces import IContentListingObject
from ftw.solr.browser.search import prepare_SearchableText


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
        flare = IContentListingObject(flare)
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
        flare = IContentListingObject(flare)
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
        flare = IContentListingObject(flare)
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

    def test_suggestions_without_solr_response(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        view = getMultiAdapter((portal, request), name=u'search')
        self.assertEquals([], view.suggestions())

    def test_appended_searchterm_does_preserve_a_valid_url(self):
        portal = self.layer['portal']
        request = self.layer['request']

        # Setup browser layers
        notify(BeforeTraverseEvent(portal, request))

        flare = PloneFlare(portal)
        flare.request = request
        flare.getURL = lambda: 'http://nohost/plone/object?this=that#ananans'
        request.form['SearchableText'] = 'test'

        content_listing = IContentListingObject(flare)
        # patch away non-relevant check
        content_listing.is_external = lambda: True

        self.assertEqual(
            content_listing.result_url(),
            'http://nohost/plone/object?this=that&searchterm=test#ananans')

    def test_breadcrumbs_escaped(self):
        """We get mixed html and plaintext form solr and need to escape the
        text. The only html we get is <em> and </em>, so we should only keep
        that unescaped.
        """
        portal = self.layer['portal']
        request = self.layer['request']
        view = getMultiAdapter((portal, request), name=u'search')
        self.assertEquals(
            '&lt;a&gt;foo&lt;/a&gt;',
            view.escape_snippet_text('<a>foo</a>'))

        self.assertEquals(
            'a &amp; b',
            view.escape_snippet_text('a & b'))

        self.assertEquals(
            'foo &lt; <em>bar</em>',
            view.escape_snippet_text('foo < <em>bar</em>'))

        self.assertEquals(
            '1 <em>foo</em> 2 <em>foo</em> 3',
            view.escape_snippet_text('1 <em>foo</em> 2 <em>foo</em> 3'))


class TestPrepareSearchableText(TestCase):

    def test_replace_inavlid_chars_with_whitespace(self):
        self.assertEquals("D abcd", prepare_SearchableText("D'abcd"))

        self.assertEquals("10 000", prepare_SearchableText("10'000"))

        self.assertEquals("hans@peter.com",
                          prepare_SearchableText("hans@peter.com"))

        self.assertEquals("strange- strange",
                          prepare_SearchableText("strange-,strange"))

        self.assertEquals("singlequoted",
                          prepare_SearchableText("'singlequoted'"))

        self.assertEquals("doublequoted",
                          prepare_SearchableText('"doublequoted"'))

        self.assertEquals("The list  one",
                          prepare_SearchableText('The list: one'))

    def test_strip_whitespace(self):

        self.assertEquals("strange-", prepare_SearchableText("strange-, "))

        self.assertEquals("text", prepare_SearchableText("    text   "))

        self.assertEquals("text   text",
                          prepare_SearchableText("  text   text"))

    def test_umlauts(self):
        self.assertEquals("\xc3\xb6 text",
                          prepare_SearchableText("    \xc3\xb6 text   "))

    def test_unicode_input(self):
        self.assertEquals("\xc3\xb6 text",
                          prepare_SearchableText(u"    \xf6 text   "))

    def test_replace_multispace_with_whitespace(self):

        multispace = u'\u3000'.encode('utf-8')
        self.assertEquals("text text",
                          prepare_SearchableText("text" + multispace + "text"))
