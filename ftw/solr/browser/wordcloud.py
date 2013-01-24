from collective.solr.browser.facets import facetParameters
from collective.solr.interfaces import ISolrConnectionManager
from itertools import islice
from math import ceil
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryUtility
from zope.publisher.browser import BrowserView
import json
import requests


CLOUD_TERMS_FIELD = 'wordCloudTerms'


class WordCloudView(BrowserView):
    """BrowserView to fetch data for and render a Word Cloud.

    Currently term frequency across all documents indexed in Solr is used as
    basis for the terms weights.
    """
    fragment_template = ViewPageTemplateFile('wordcloud_fragment.pt')
    debug_template = ViewPageTemplateFile('wordcloud_debug.pt')

    def get_scale(self, weight):
        """Scale term size according to its weight.
        """
        n = self.options['num_sizes']
        # Scale linearly for now
        scale = ceil(weight * n) / n
        return scale

    def get_style(self, weight):
        """Given a specific term weight, return CSS styles that format an <a>
        element accordingly.
        """
        scale = self.get_scale(weight)

        # Size in percent of inherited font size
        size = int(100 * scale)

        # Scale by configurable constant factor
        size *= self.options['scale_factor']

        return 'font-size: %s%%; border-bottom:0; text-decoration: none' % size

    def get_solr_terms_handler_url(self):
        """Construct the URL to the Solr 'terms' request handler.
        """
        manager = queryUtility(ISolrConnectionManager)
        conn = manager.getConnection()
        if conn is None:
            raise Exception("Couldn't get a Solr connection. Please make sure "
                            "Solr is installed and activated.")
        url = "http://%s%s/terms" % (conn.host, conn.solrBase)
        return url

    def get_terms(self):
        """Return a dictionary of term:count pairs, where `term` is the term's
        name and `count` the number of times the term appears across all
        documents.
        """
        num_words = self.options['num_words']
        params = {'terms.fl': CLOUD_TERMS_FIELD,
                  'terms.limit': num_words,
                  'wt': 'json'}
        url = self.get_solr_terms_handler_url()
        response = requests.post(url, data=params)
        data = response.content
        results = json.loads(data)

        response_header = results['responseHeader']
        if not response_header['status'] == 0:
            # TODO Better exception handling
            raise Exception(str(response_header))

        terms = results['terms'][CLOUD_TERMS_FIELD]

        # terms is a list of [key1, val1, key2, val2, ...]
        # so we extract keys and values and zip() them into a dict
        keys = islice(terms, 0, None, 2)
        values = islice(terms, 1, None, 2)
        cloud_terms = {}
        for pair in zip(keys, values):
            term, count = pair
            cloud_terms[term] = count

        return cloud_terms

    def get_weighted_terms(self):
        """Return a list of term dictionaries including the relative weight
        of the term.
        """
        terms = self.get_terms()
        max_count = max(terms.values())

        weighted_terms = []
        for term, count in terms.items():
            weight = float(count) / max_count
            style = self.get_style(weight)
            weighted_terms.append({'name': term,
                                   'count': count,
                                   'weight': weight,
                                   'style': style})
        # Sort alphabetically by term name by default.
        # If further post-processing in python is required, this will need to
        # be changed to sort by count (reversed).
        weighted_terms.sort(key=lambda x: x['name'])
        return weighted_terms

    def search_url(self):
        """Construct the URL that will be used to link cloud terms to a search
        for that term. Assumes the search term will be appended at the end.
        """
        portal_url = getToolByName(self.context, 'portal_url')
        base_url = portal_url.getPortalObject().absolute_url()
        url = "%s/@@search?" % base_url

        # Add faceting parameters
        facets, dependencies = facetParameters(self.context, self.request)
        url += '&facet=true'
        for facet in facets:
            url += '&facet.field=%s' % facet

        url += '&SearchableText='
        return url

    def _parse_option(self, key, kwargs, default):
        """Parses options needed for the WordCloudView and stores them in the
        self.options dict.

        Values received in request.form have the highest priority and override
        options passed in as keyword arguments to the call() method. If no
        value for an option is supplied in the request, the kwarg is used. If
        there's no kwarg either, we fall back to `default`.

        After parsing the options and populating self.options, kwargs should be
        updated with self.options.
        """
        request_value = self.request.form.get(key)
        if request_value not in (None, ''):
            value = request_value
        else:
            value = kwargs.get(key, default)
        self.options[key] = value

    def __call__(self, *args, **kwargs):
        self.options = {}
        self._parse_option('num_words', kwargs, 10)
        self._parse_option('num_sizes', kwargs, 5)
        self._parse_option('scale_factor', kwargs, 2.0)
        kwargs.update(self.options)

        if self.request.form.get('raw'):
            # Raw output - return weighted terms as pretty printed JSON
            return json.dumps(self.get_weighted_terms(),
                              sort_keys=True,
                              indent=4,
                              separators=(',', ': '))

        elif self.request.form.get('debug'):
            # Debug output - wrap the fragment with a debug template to get a
            # complete HTML document
            return self.debug_template(self, **kwargs)

        # Standard fragment template - only for inclusion in an existing HTML
        # document (as a portlet for example.)
        return self.fragment_template(self, **kwargs)
