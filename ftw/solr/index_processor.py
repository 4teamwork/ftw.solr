from collective.solr.indexer import SolrIndexProcessor
from collective.solr.interfaces import ISolrIndexQueueProcessor
from zope.interface import implements


# TODO: Remove whole file in next major release.


class FtwSolrIndexProcessor(SolrIndexProcessor):
    implements(ISolrIndexQueueProcessor)
