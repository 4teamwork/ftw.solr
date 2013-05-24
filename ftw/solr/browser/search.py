from logging import getLogger
from plone.app.search import browser
from plone.app.contentlisting.interfaces import IContentListing
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.PloneBatch import Batch
from Products.ZCTextIndex.ParseTree import ParseError
from plone.app.layout.viewlets import common
from collective.solr.solr import SolrException
from collective.solr.browser.facets import FacetMixin

logger = getLogger('ftw.solr')


class SearchView(browser.Search):

    template = ViewPageTemplateFile('search.pt')
    results_template = ViewPageTemplateFile('results.pt')

    def __call__(self):
        if 'ajax' in self.request.form:
            del self.request.form['ajax']
            # Disable theming for ajax requests
            self.request.response.setHeader('X-Theme-Disabled', 'True')
            return self.results_template()
        return self.template()

    def render_results(self):
        return self.results_template()

    def results(self, query=None, batch=True, b_size=10, b_start=0):
        """Get properly wrapped search results from the catalog.
        'query' should be a dictionary of catalog parameters.
        """
        # Disable theming for ajax requests
        if 'ajax' in self.request.form:
            del self.request.form['ajax']
            self.request.response.setHeader('X-Theme-Disabled', 'True')

        if query is None:
            query = {}

        query['b_start'] = b_start = int(b_start)
        query['b_size'] = b_size
        query = self.filter_query(query)

        if query is None:
            results = []
        else:
            query.update({'qt': 'hlsearch'});
            catalog = getToolByName(self.context, 'portal_catalog')
            try:
                results = catalog(**query)
            except ParseError:
                logger.exception('Exception while searching')
                return []
            except SolrException:
                logger.exception('Exception while searching')
                return []

        self.solr_response = results
        results = IContentListing(results)
        if batch:
            results = Batch(results, b_size, b_start)
        return results

    def snippets(self):
        """Return snippets with highlighted search terms in a dict with the
           item's UID as key and the snippet text as value.
        """
        if not hasattr(self, 'solr_response'):
            return {}
        if hasattr(self.solr_response, 'highlighting'):
            joined_snippets = {}
            for uid, snippets in self.solr_response.highlighting.items():
                joined_snippets[uid] = ' '.join([' '.join(snippet) for snippet
                                                in snippets.values()]).strip()
            return joined_snippets
        return {}

    def suggestions(self):
        """Get suggestions from spellcheck component.
        """
        suggested_terms = []
        search_terms = [term.lower() for term in self.request.form.get('SearchableText', '').split()]
        query_params = self.request.form.copy()
        if hasattr(self.solr_response, 'spellcheck'):
            suggestions = self.solr_response.spellcheck.get('suggestions', [])
            for term in search_terms:
                if term in suggestions:
                    suggestion = suggestions[term]['suggestion']
                    query_params['SearchableText'] = suggestion[0]['word']
                    query_string = ''
                    for k,v in query_params.items():
                        if isinstance(v, list):
                            query_string += '&'.join(['%s=%s' % (k,vv) for vv in v])
                        else:
                            query_string += '&%s=%s' % (k,v)
                    suggested_terms.append((suggestion[0]['word'], query_string))
        return suggested_terms


class SearchBoxViewlet(common.SearchBoxViewlet, FacetMixin):

    index = ViewPageTemplateFile('searchbox.pt')
