# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
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

    def search(query, **parameters):
        """Perform a search with the given querystring and extra parameters"""
