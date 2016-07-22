# -*- coding: utf-8 -*-
from collective.solr.exceptions import SolrConnectionException
from ftw.solr.interfaces import ISearchSettings
from logging import getLogger
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.search import browser
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.PloneBatch import Batch
from Products.CMFPlone.utils import safe_hasattr
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.ZCTextIndex.ParseTree import ParseError
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.deferredimport import deprecated
import urllib
import urlparse


logger = getLogger('ftw.solr')


deprecated(
    "This class is moved to another place. "
    "Please use ftw.solr.viewlets.searchbox.SearchBoxViewlet instead",
    SearchBoxViewlet='ftw.solr.viewlets.searchbox:SearchBoxViewlet')


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

    def filter_query(self, query):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSettings)

        query = super(SearchView, self).filter_query(query)
        if settings.respect_navroot:
            # If respect_navroot is enabled, return the filtered query
            # unchanged
            return query

        # Otherwise, if there wasn't a path filter in the query before,
        # remove the path filter that filter_query() put in.
        if query and 'path' in query and 'path' not in self.request.form:
            query.pop('path')
        return query

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
            query.update({'request_handler': 'hlsearch'})
            catalog = getToolByName(self.context, 'portal_catalog')
            try:
                results = catalog(**query)
            except ParseError:
                logger.exception('Exception while searching')
                return []
            except SolrConnectionException:
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
        if not safe_hasattr(self, 'solr_response'):
            return {}
        if safe_hasattr(self.solr_response, 'highlighting'):
            joined_snippets = {}
            for uid, snippets in self.solr_response.highlighting.items():
                joined_snippets[uid] = ' '.join([' '.join(snippet) for snippet
                                                 in snippets.values()]).strip()
            return joined_snippets
        return {}

    def suggestions(self):
        """Get suggestions from spellcheck component.
        """
        if not safe_hasattr(self, 'solr_response'):
            return []

        suggested_terms = []
        search_terms = [term.lower() for term in self.request.form.get(
            'SearchableText', '').split()]
        query_params = self.request.form.copy()

        if safe_hasattr(self.solr_response, 'spellcheck'):
            suggestions = self.solr_response.spellcheck.get('suggestions', [])
            for term in search_terms:
                if term in suggestions:
                    suggestion = suggestions[term]['suggestion']
                    query_params['SearchableText'] = suggestion[0]['word']
                    query_string = ''
                    for k, v in query_params.items():
                        if isinstance(v, list):
                            query_string += '&' + '&'.join(
                                ['%s=%s' % (k, vv) for vv in v])
                        else:
                            query_string += '&%s=%s' % (k, v)
                    suggested_terms.append((suggestion[0]['word'],
                                            query_string))
        return suggested_terms

    def breadcrumbs(self, item):
        if hasattr(item, 'is_external') and item.is_external():
            return None

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISearchSettings)
        maxb = settings.max_breadcrumbs

        if settings.path_based_breadcrumbs:
            portal_url = getToolByName(self.context, 'portal_url')
            portal = portal_url.getPortalObject()
            portal_path = portal_url.getPortalPath()
            path = item.getPath()[len(portal_path):]
            breadcrumbs = []
            url = portal.absolute_url()
            for part in path.split('/')[1:-1]:
                url = '%s/%s' % (url, part)
                breadcrumbs.append({
                    'Title': part,
                    'absolute_url': url,
                })
        else:
            obj = item.getObject()
            view = getMultiAdapter((obj, self.request),
                                   name='breadcrumbs_view')
            # cut off the item itself
            breadcrumbs = list(view.breadcrumbs())[:-1]

        if len(breadcrumbs) == 0:
            # don't show breadcrumbs if we only have a single element
            return None
        if len(breadcrumbs) > maxb:
            # if we have too long breadcrumbs, emit the middle elements
            empty = {'absolute_url': '', 'Title': unicode('…', 'utf-8')}
            breadcrumbs = [breadcrumbs[0], empty] + breadcrumbs[-maxb + 1:]
        return breadcrumbs

    def remove_path_link_info(self):
        query_dict = urlparse.parse_qs(self.request.get('QUERY_STRING', ''))

        if 'path' not in query_dict:
            return None

        path = query_dict['path']

        # Path may be a list, but wie deal only with the first item anyway
        path = isinstance(path, list) and path[0] or path
        item = self.context.unrestrictedTraverse(path)
        del query_dict['path']

        return {'search_url': '{0}?{1}'.format(self.request.get('ACTUAL_URL'),
                                               urllib.urlencode(query_dict, doseq=True)),
                'title': item.Title(),
                'url': item.absolute_url()}
