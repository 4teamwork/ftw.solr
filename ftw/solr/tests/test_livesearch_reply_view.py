# -*- coding: utf-8 -*-
from ftw.solr.testing import SOLR_INTEGRATION_TESTING
from unittest2 import TestCase
from ftw.solr.browser.livesearch import LiveSearchReplyView
from lxml import html as parser


class TestGetShowMoreLink(TestCase):

    layer = SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.context = LiveSearchReplyView(object, object)

    def test_has_linktext(self):
        result = self.context.get_show_more_link('show all')

        self.assertEqual('show all', parser.fromstring(result).text)

    def test_has_search_term(self):
        result = self.context.get_show_more_link(searchterms="james")

        self.assertIn(
            'SearchableText=james',
            parser.fromstring(result).attrib.get('href'))

    def test_has_path_parameter_if_path_is_set(self):
        result = self.context.get_show_more_link(path='/path/to/context')

        self.assertIn(
            'path=%2Fpath%2Fto%2Fcontext',
            parser.fromstring(result).attrib.get('href'))

    def test_has_no_path_parameter_if_no_path_is_set(self):
        result = self.context.get_show_more_link()

        self.assertNotIn(
            'path=',
            parser.fromstring(result).attrib.get('href'))

    def test_has_facet_params(self):
        result = self.context.get_show_more_link(
            facet_params='facet.area=true')

        self.assertIn(
            'facet.area=true',
            parser.fromstring(result).attrib.get('href'))
