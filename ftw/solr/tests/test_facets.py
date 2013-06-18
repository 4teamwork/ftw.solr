from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.parser import SolrResponse
from ftw.solr.browser.facets import SearchFacetsView
from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from ftw.solr.tests.utils import getData
from unittest2 import TestCase
from zope.component import queryUtility


class TestFacetsView(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_facets_order(self):
        portal = self.layer['portal']
        request = self.layer['request']
        request.form.update({'facet_field': ['type', 'section', 'topics']})
        response = SolrResponse(getData('facets_response.xml'))
        view = SearchFacetsView(portal, request)
        view.kw = dict(results=response)

        config = queryUtility(ISolrConnectionConfig)
        config.facets = ['type', 'section', 'topics']
        facets = view.facets()
        self.assertEquals(['type', 'section', 'topics'],
            [facets[0]['title'], facets[1]['title'], facets[2]['title']],
            msg='Wrong facet order.')

        config.facets = ['section', 'topics', 'type']
        facets = view.facets()
        self.assertEquals(['section', 'topics', 'type'],
            [facets[0]['title'], facets[1]['title'], facets[2]['title']],
            msg='Wrong facet order.')
