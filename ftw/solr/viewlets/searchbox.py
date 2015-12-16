from plone.app.layout.viewlets import common
from collective.solr.browser.facets import FacetMixin


class SearchBoxViewlet(common.SearchBoxViewlet, FacetMixin):
    """
    """
    # def initial_site_area_filter(self):
    #     if 'facet.field' in self.request.form:
    #         return None
    #     obj = aq_inner(self.context)

    #     if IPloneSiteRoot.providedBy(api.portal.get_navigation_root(obj)):
    #         return None
    #     else:
    #         return site_area_indexer(obj)()

    # def hiddenfields(self):
    #     facets, dependencies = facetParameters(self)
    #     facets = list(facets)
    #     queries = param(self, 'fq')
    #     site_area = self.initial_site_area_filter()
    #     if site_area:
    #         queries = ['site_area:"%s"' % site_area]
    #         if 'site_area' in facets:
    #             facets.remove('site_area')

    #     return self.hidden(facets=facets, queries=queries)
