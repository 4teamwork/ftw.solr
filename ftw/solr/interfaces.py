# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import getFSVersionTuple
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema import Bool
from zope.schema import Text


PLONE51 = getFSVersionTuple() >= (5, 1)
if PLONE51:
    from Products.CMFCore.interfaces import IIndexQueueProcessor
else:
    from collective.indexing.interfaces import IIndexQueueProcessor


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

    def search(request_handler=u'/select', query=u'*:*', filters=None,
               start=0, rows=1000, sort=None, **params):
        """Perform a search with the given querystring and extra parameters"""


class ISolrDocument(Interface):
    """Solr document"""


class ISolrSettings(Interface):

    enabled = Bool(
        title=u'Enable Indexing',
        description=u'Check this to enable indexing in Solr.',
        default=True,
    )

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
                    u'{term} will be replaced with the search term.',
        default=u'Title:{term}^100 OR Title:{term}*^10 '
                u'OR SearchableText:{term}^10 OR SearchableText:{term}*',
    )

    simple_search_phrase_pattern = Text(
        title=u'Simple Search Phrase Pattern',
        description=u'Pattern used with the whole search phrase in a simple '
                    u'search query. {phrase} will be replaced with the search '
                    u'phrase. Use this to boost the whole phrase more than the'
                    u'single terms.',
        default=u'Title:"{phrase}"^500 OR Title:"{phrase}*"^200 '
                u'OR SearchableText:"{phrase}"^200 '
                u'OR SearchableText:"{phrase}*"^20',
    )

    complex_search_pattern = Text(
        title=u'Complex Search Pattern',
        description=u'Pattern for complex search queries containing boolean '
                    u'operators. {phrase} will be replaced with the search '
                    u'query.',
        default=u'Title:({phrase})^10 OR SearchableText:({phrase})',
    )

    enable_updates_in_post_commit_hook = Bool(
        title=u'Enable performing update operations in a post commit hook.',
        description=u'Check this to allow performing update operations in a '
                    u'post commit hook. This allows to optimize the time the '
                    u'zodb is locked.',
        default=True,
    )
