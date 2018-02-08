from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexHandler
from ftw.solr.interfaces import ISolrIndexQueueProcessor
from logging import getLogger
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.interface import implementer


logger = getLogger('ftw.solr.indexer')


@implementer(ISolrIndexQueueProcessor)
class SolrIndexQueueProcessor(object):
    """A queue processor for solr """

    _manager = None

    def index(self, obj, attributes=None):
        """Index the given object."""
        handler = getMultiAdapter((obj, self.manager), ISolrIndexHandler)
        handler.add(attributes)

    def reindex(self, obj, attributes=None):
        """Reindex the given object."""
        self.index(obj, attributes)

    def unindex(self, obj):
        """Unindex the given object."""
        handler = getMultiAdapter((obj, self.manager), ISolrIndexHandler)
        handler.delete()

    def begin(self):
        """Called before processing of the queue is started."""
        pass

    def commit(self):
        """Called after processing of the queue has ended."""
        conn = self.manager.connection
        if conn is None:
            return
        conn.commit()

    def abort(self):
        """Called if processing of the queue needs to be aborted."""
        conn = self.manager.connection
        if conn is None:
            return
        conn.abort()

    @property
    def manager(self):
        if self._manager is None:
            self._manager = queryUtility(ISolrConnectionManager)
        return self._manager
