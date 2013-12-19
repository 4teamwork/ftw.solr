# -*- coding: utf-8 -*-
from ftw.solr.testing import SOLR_INTEGRATION_TESTING
from unittest2 import TestCase
from ftw.solr.browser.livesearch import LiveSearchReplyView
from lxml import html as parser


class TestGetShowMoreLink(TestCase):

    layer = SOLR_INTEGRATION_TESTING

    def setUp(self):
        request = self.layer['request']
        self.livesearch = LiveSearchReplyView(object, request)
        self.livesearch.facet_params = 'facet.field=portal_type'
        self.livesearch.searchterms = 'james'
        

    def test_has_linktext(self):
        result = self.livesearch.get_show_more_link()

        self.assertEqual('Show all items', parser.fromstring(result).text)

    def test_has_search_term(self):
        result = self.livesearch.get_show_more_link()

        self.assertIn(
            'SearchableText=james',
            parser.fromstring(result).attrib.get('href'))

    def test_has_path_parameter_if_path_is_set(self):
        self.livesearch.request.form.update({'path':'/path/to/context',})
        result = self.livesearch.get_show_more_link()

        self.assertIn(
            'path=%2Fpath%2Fto%2Fcontext',
            parser.fromstring(result).attrib.get('href'))

    def test_has_no_path_parameter_if_no_path_is_set(self):
        result = self.livesearch.get_show_more_link()

        self.assertNotIn(
            'path=',
            parser.fromstring(result).attrib.get('href'))

    def test_has_facet_params(self):
        result = self.livesearch.get_show_more_link()

        self.assertIn(
            'facet.field=portal_type',
            parser.fromstring(result).attrib.get('href'))
