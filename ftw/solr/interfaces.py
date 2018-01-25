# -*- coding: utf-8 -*-
from collective.indexing.interfaces import IIndexQueueProcessor
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema import Text


class IFtwSolrLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class ISolrIndexQueueProcessor(IIndexQueueProcessor):
    """Solr index queue processor"""


class ISolrConnectionManager(Interface):
    """Solr connection manager"""


class ISolrConnectionConfig(Interface):
    """Solr connection configuration"""


class ISolrIndexHandler(Interface):
    """Handles uploading of data in Solr"""


class ISolrSearch(Interface):
    """Solr search utility"""

    def search(query, **parameters):
        """Perform a search with the given querystring and extra parameters"""


class ISolrSettings(Interface):

    local_query_parameters = Text(
        title=u'Local Query Parameters',
        description=u"Prefixes the query string with local parameters. Must "
                    u"begin with '{!' and end with '}'.",
        default=u'{!boost b=recip(ms(NOW,modified),3.858e-10,10,1)}',
        required=False,
    )

    simple_search_term_pattern = Text(
        title=u'Simple Search Term Pattern',
        description=u'Pattern applied to every term of a simple search query.'
                    u'{term} will be replaced with the search term stripped of'
                    u' any wildcard symbols.',
        default=u'Title:{term}^100 OR Title:{term}*^10 '
                u'OR SearchableText:{term}^10 OR SearchableText:{term}*',
    )

    simple_search_phrase_pattern = Text(
        title=u'Simple Search Phrase Pattern',
        description=u'Pattern used with the whole search term in a simple '
                    u'search query. {phrase} will be replaced with the search '
                    u'term stripped of any wildcard symbols.',
        default=u'Title:{phrase}^200 OR Title:{phrase}*^20 '
                u'OR SearchableText:{phrase}^20 OR SearchableText:{phrase}*^2',
    )

    complex_search_pattern = Text(
        title=u'Complex Search Pattern',
        description=u'Pattern for complex search queries containing boolean '
                    u'operators. {term} will be replaced with the search term',
        default=u'Title:({term})^10 OR SearchableText:({term})',
    )
