from collective.solr.parser import SolrResponse
from ftw.solr import IS_PLONE_5
from ftw.solr.browser.facets import SearchFacetsView
from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from ftw.solr.tests.utils import getData
from unittest2 import TestCase


class TestFacetsView(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_facets_order(self):
        portal = self.layer['portal']
        request = self.layer['request']
        request.form.update({'facet_field': ['type', 'section', 'topics']})
        response = SolrResponse(getData('facets_response.xml'))
        view = SearchFacetsView(portal, request)
        view.kw = dict(results=response)

        if IS_PLONE_5:
            from collective.solr.utils import getConfig
            config = getConfig()
        else:
            from collective.solr.interfaces import ISolrConnectionConfig
            from zope.component import getUtility
            config = getUtility(ISolrConnectionConfig)

        config.facets = [u'type', u'section', u'topics']
        facets = view.facets()
        self.assertEquals([u'type', u'section', u'topics'],
                          [facets[0]['title'], facets[1]['title'], facets[2]['title']],
                          msg='Wrong facet order.')

        config.facets = [u'section', u'topics', u'type']
        facets = view.facets()
        self.assertEquals(['section', 'topics', 'type'],
                          [facets[0]['title'], facets[1]['title'], facets[2]['title']],
                          msg='Wrong facet order.')
