from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexHandler
from logging import getLogger
from Products.CMFCore.interfaces import ICatalogAware
from Products.CMFPlone.utils import base_hasattr
from Products.Five.browser import BrowserView
from time import clock
from time import strftime
from time import time
from zope.component import getMultiAdapter
from zope.component import queryUtility
import logging

logger = getLogger('ftw.solr.maintenance')
logger.setLevel(logging.DEBUG)


def timer(func=time):
    """Set up a generator returning the elapsed time since the last call """
    def gen(last=func()):
        while True:
            elapsed = func() - last
            last = func()
            yield '%.3fs' % elapsed
    return gen()


def checkpoint_iterator(function, interval=100):
    """The iterator will call the given function for every nth invocation """
    counter = 0
    while True:
        counter += 1
        if counter % interval == 0:
            function()
        yield None


class SolrMaintenanceView(BrowserView):
    """Helper view for indexing content in Solr."""

    def __init__(self, context, request):
        super(SolrMaintenanceView, self).__init__(context, request)
        self.request.RESPONSE.setHeader('Content-Type', 'text/plain')

    def optimize(self):
        """Optimize the Solr index."""
        conn = self.manager.connection
        conn.post('/update', data={'optimize': {'waitSearcher': False}})
        return 'Solr index optimized.'

    def clear(self):
        """Clear all data from Solr index."""
        conn = self.manager.connection
        conn.delete_by_query('*:*')
        conn.commit()
        return 'Solr index cleared.'

    def reindex(self):
        """Reindex content in Solr."""

        processed = 0
        real = timer()
        lap = timer()
        cpu = timer(clock)

        def commit():
            conn = self.manager.connection
            conn.commit(extract_after_commit=False)
            self.log(
                'Intermediate commit (%d items processed, last batch in %s)',
                processed, lap.next())

        cpi = checkpoint_iterator(commit)
        self.log('Reindexing Solr...')
        for path, obj in find_objects(self.context):

            if not ICatalogAware.providedBy(obj):
                continue

            attributes = None
            handler = getMultiAdapter((obj, self.manager), ISolrIndexHandler)
            handler.add(attributes)
            processed += 1
            cpi.next()

        commit()
        self.log('Solr index rebuilt.')
        self.log(
            'Processed %d items in %s (%s cpu time).',
            processed, real.next(), cpu.next())

    def log(self, msg, *args):
        logger.info(msg, *args)
        self.request.RESPONSE.write(
            strftime('%Y-%m-%d %H:%M:%S ') + msg % args + '\n')

    @property
    def manager(self):
        return queryUtility(ISolrConnectionManager)


def find_objects(context):
    """Generator to recursively find and yield all objects below the given
       context."""
    traverse = context.unrestrictedTraverse
    base = '/'.join(context.getPhysicalPath())
    cut = len(base) + 1
    paths = [base]
    for idx, path in enumerate(paths):
        obj = traverse(path)
        yield path[cut:], obj
        if base_hasattr(obj, 'objectIds'):
            for id_ in obj.objectIds():
                paths.insert(idx + 1, path + '/' + id_)