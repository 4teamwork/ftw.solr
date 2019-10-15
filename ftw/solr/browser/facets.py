from urllib import urlencode
from copy import deepcopy
from plone.memoize.view import memoize
from zope.component import getUtility, queryUtility
from zope.i18n import translate
from zope.i18nmessageid import Message

from collective.solr.browser import facets
from collective.solr.browser.facets import param, facetParameters
from collective.solr.interfaces import IFacetTitleVocabularyFactory
from ftw.solr import IS_PLONE_5


FACET_QUERY_POSITIONS = {
    '[NOW/DAY TO *]': 0,
    '[NOW/DAY-1DAY TO NOW/DAY]': 1,
    '[NOW/DAY-7DAYS TO *]': 2,
    '[NOW/DAY-1MONTH TO *]': 3,
    '[NOW/DAY-1YEAR TO *]': 4,
}


class SearchFacetsView(facets.SearchFacetsView):

    @memoize
    def facet_queries(self):
        """Extract facet queries from results.
        """
        results = self.kw.get('results', None)
        fcs = getattr(results, 'facet_counts', None)
        if results is None or fcs is None:
            return None

        fqueries = fcs.get('facet_queries', {})
        facets = {}
        for fquery, count in fqueries.items():
            if count < 1:
                continue
            facet_title, item_title = fquery.split(':', 1)
            if facet_title not in facets:
                facets[facet_title] = {}
            facets[facet_title][item_title] = count
        return facets

    def facets(self):
        """Prepare and return facetting info for the given SolrResponse """

        # Facets should always return a list. But it returns None if there are no
        # facets. This will cause problems because of inconsistent types.
        info = super(SearchFacetsView, self).facets() or []
        facet_queries = self.facet_queries()
        if not facet_queries:
            return info

        params = self.request.form.copy()
        if 'b_start' in params:
            del params['b_start'] # Clear the batch when limiting a result set
        fq = params.get('fq', [])
        if isinstance(fq, basestring):
            fq = params['fq'] = [fq]
        selected = set([facet.split(':', 1)[0] for facet in fq])

        for facet_title, facet_counts in facet_queries.items():
            if facet_title in selected:
                continue
            counts = []

            # Look up a vocabulary to provide a title for this facet
            vfactory = queryUtility(IFacetTitleVocabularyFactory, name=facet_title)
            if vfactory is None:
                # Use the default fallback
                vfactory = getUtility(IFacetTitleVocabularyFactory)
            vocabulary = vfactory(self.context)

            for name, count in facet_counts.items():
                p = deepcopy(params)
                p.setdefault('fq', []).append('%s:%s' % (facet_title, name.encode('utf-8')))

                title = name
                if name in vocabulary:
                    title = vocabulary.getTerm(name).title
                if isinstance(title, Message):
                    title = translate(title, context=self.request)

                counts.append(dict(
                    name=name,
                    title=title,
                    count=count,
                    query=urlencode(p, doseq=True),
                ))
            info.append(dict(title=facet_title, counts=sorted(counts,
                key=lambda x: FACET_QUERY_POSITIONS.get(x['name'], 100))))

        # Sort facets in the order stored in the configuration
        if IS_PLONE_5:
            from collective.solr.utils import getConfig
            config = getConfig()
        else:
            from collective.solr.interfaces import ISolrConnectionConfig
            config = queryUtility(ISolrConnectionConfig)

        if config is not None:
            def pos(item):
                try:
                    return config.facets.index(item['title'])
                except ValueError:
                    return len(config.facets)
            info.sort(key=pos)

        return info

    def selected(self):
        """Determine selected facets and prepare links to clear them;
           this assumes that facets are selected using filter queries."""
        info = []
        facets = param(self, 'facet.field')
        facet_queries = self.facet_queries() or []
        fq = param(self, 'fq')
        for idx, query in enumerate(fq):
            field, value = query.split(':', 1)
            params = self.request.form.copy()
            params['fq'] = fq[:idx] + fq[idx+1:]

            # Facet queries are handled slightly different
            # (they are not enclosed by double quotes)
            if field in facet_queries:
                # Look up a vocabulary to provide a title for this facet
                vfactory = queryUtility(IFacetTitleVocabularyFactory, name=field)
                if vfactory is None:
                    # Use the default fallback
                    vfactory = getUtility(IFacetTitleVocabularyFactory)
                vocabulary = vfactory(self.context)
                if value in vocabulary:
                    value = vocabulary.getTerm(value).title
                if isinstance(value, Message):
                    value = translate(value, context=self.request)

                info.append(dict(title=field, value=value,
                    query=urlencode(params, doseq=True)))
                continue

            # Facet fields
            if field not in facets:
                params['facet.field'] = facets + [field]
            if value.startswith('"') and value.endswith('"'):
                # Look up a vocabulary to provide a title for this facet
                vfactory = queryUtility(IFacetTitleVocabularyFactory, name=field)
                if vfactory is None:
                    # Use the default fallback
                    vfactory = getUtility(IFacetTitleVocabularyFactory)
                vocabulary = vfactory(self.context)
                value = value[1:-1]
                if value in vocabulary:
                    value = vocabulary.getTerm(value.decode('utf8')).title
                if isinstance(value, Message):
                    value = translate(value, context=self.request)

                info.append(dict(title=field, value=value,
                    query=urlencode(params, doseq=True)))

        return info

    def facet_parameters(self):
        """Return the facet parameters to be queried for as an url-encoded
           string.
        """
        facets, dependencies = facetParameters(self)
        return urlencode({'facet': 'true', 'facet.field': facets, },
                         doseq=True)
