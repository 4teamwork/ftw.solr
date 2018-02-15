from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexHandler
from logging import getLogger
from Products.CMFCore.interfaces import ICatalogAware
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.Five.browser import BrowserView
from time import clock
from time import strftime
from time import time
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.component.hooks import getSite
import logging
import transaction


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
        conn.optimize()
        return 'Solr index optimized.'

    def clear(self):
        """Clear all data from Solr index."""
        conn = self.manager.connection
        conn.delete_by_query('*:*')
        conn.commit()
        return 'Solr index cleared.'

    def reindex(self, commit_interval=100, idxs=None):
        """Reindex content in Solr."""

        processed = 0
        real = timer()
        lap = timer()
        cpu = timer(clock)

        transaction.doom()
        zodb_conn = self.context._p_jar

        def commit():
            conn = self.manager.connection
            conn.commit(extract_after_commit=False)
            zodb_conn.cacheGC()
            self.log(
                'Intermediate commit (%d items processed, last batch in %s)',
                processed, lap.next())

        cpi = checkpoint_iterator(commit, interval=commit_interval)
        self.log('Reindexing Solr...')
        for path, obj in find_objects(self.context):

            if not ICatalogAware.providedBy(obj):
                continue

            handler = getMultiAdapter((obj, self.manager), ISolrIndexHandler)
            handler.add(idxs)
            processed += 1
            cpi.next()

        commit()
        self.log('Solr index rebuilt.')
        self.log(
            'Processed %d items in %s (%s cpu time).',
            processed, real.next(), cpu.next())

    def reindex_cataloged(self, commit_interval=100, idxs=None, start=0,
                          end=-1):
        """Reindex all cataloged content in Solr."""
        site = getSite()
        catalog = getToolByName(self.context, 'portal_catalog')
        items = catalog.unrestrictedSearchResults(sort_on='path')

        try:
            start = int(start)
            end = int(end)
            commit_interval = int(commit_interval)
        except ValueError:
            start = 0
            end = -1
            commit_interval = 100

        processed = 0
        real = timer()
        lap = timer()
        cpu = timer(clock)

        transaction.doom()
        zodb_conn = self.context._p_jar

        def commit():
            conn = self.manager.connection
            conn.commit(extract_after_commit=False)
            zodb_conn.cacheGC()
            self.log(
                'Intermediate commit (%d items processed, last batch in %s)',
                processed, lap.next())

        cpi = checkpoint_iterator(commit, interval=commit_interval)
        self.log('Reindexing Solr...')
        for item in items[start:end]:
            path = item.getPath()
            obj = site.unrestrictedTraverse(path, None)
            if obj is None:
                logger.warning("Object at path %s doesn't exist", path)
                continue

            handler = getMultiAdapter((obj, self.manager), ISolrIndexHandler)
            handler.add(idxs)
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
