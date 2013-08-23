from collective.solr.indexer import boost_values
from collective.solr.indexer import indexable
from collective.solr.indexer import SolrIndexProcessor
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.solr import SolrException
from collective.solr.utils import prepareData
from logging import getLogger
from socket import error
from zope.component import getUtility
from zope.interface import implements


logger = getLogger('ftw.solr.index_processor')


class FtwSolrIndexProcessor(SolrIndexProcessor):
    """Index processor that can perform atomic updates.
    """

    implements(ISolrIndexQueueProcessor)

    def index(self, obj, attributes=None):
        """Index the specified attributes for obj using atomic updates, or all
        of them if `attributes` is `None`.

        Changes to the original method include making sure the uniqueKey is
        part of the attributes, and passing the attributes to the
        self.getData() call to avoid causing Plone to index all fields instead
        of just the necessary ones.
        """
        conn = self.getConnection()
        if conn is not None and indexable(obj):
            schema = self.manager.getSchema()
            if schema is None:
                msg = 'unable to fetch schema, skipping indexing of %r'
                logger.warning(msg, obj)
                return
            uniqueKey = schema.get('uniqueKey', None)
            if uniqueKey is None:
                msg = 'schema is missing unique key, skipping indexing of %r'
                logger.warning(msg, obj)
                return

            if attributes is not None:
                attributes = set(schema.keys()).intersection(attributes)
                if not attributes:
                    return
                if not uniqueKey in attributes:
                    # The uniqueKey is required in order to identify the
                    # document when doing atomic updates.
                    attributes.add(uniqueKey)

            data, missing = self.getData(obj, attributes=attributes)
            if not data:
                return          # don't index with no data...
            prepareData(data)

            if data.get(uniqueKey, None) is not None and not missing:
                config = getUtility(ISolrConnectionConfig)
                if config.commit_within:
                    data['commitWithin'] = config.commit_within
                try:
                    logger.debug('indexing %r (%r)', obj, data)
                    conn.add(boost_values=boost_values(obj, data), **data)
                except (SolrException, error):
                    logger.exception('exception during indexing %r', obj)
