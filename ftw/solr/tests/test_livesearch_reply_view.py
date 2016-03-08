from ftw.solr.browser.livesearch import FtwSolrLiveSearchReplyView
from ftw.solr.testing import SOLR_INTEGRATION_TESTING
from unittest2 import TestCase


class TestGetShowMoreLink(TestCase):

    layer = SOLR_INTEGRATION_TESTING

    def setUp(self):
        request = self.layer['request']
        self.livesearch = FtwSolrLiveSearchReplyView(object, request)
        self.livesearch.facet_params = 'facet.field=portal_type'
        self.livesearch.searchterms = 'james'

    def test_has_linktext(self):
        result = self.livesearch.get_show_more_item()

        self.assertEqual('Show all items', result.get('title'))

    def test_has_search_term(self):
        result = self.livesearch.get_show_more_item()

        self.assertIn('SearchableText=james', result.get('url'))

    def test_has_path_parameter_if_path_is_set(self):
        self.livesearch.request.form.update({'path': '/path/to/context', })
        result = self.livesearch.get_show_more_item()

        self.assertIn('path=%2Fpath%2Fto%2Fcontext', result.get('url'))

    def test_has_no_path_parameter_if_no_path_is_set(self):
        result = self.livesearch.get_show_more_item()

        self.assertNotIn('path=', result.get('url'))

    def test_has_facet_params(self):
        result = self.livesearch.get_show_more_item()

        self.assertIn('facet.field=portal_type', result.get('url'))
