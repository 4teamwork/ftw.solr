# -*- coding: utf-8 -*-
from ftw.solr.converters import to_iso8601
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


def solr_date(date):
    """Solr date representation. Fractional seconds are stripped if 0."""
    value = to_iso8601(date)
    if value.endswith('.000Z'):
        value = value[:-5] + 'Z'
    return value


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

    def reindex(self, commit_interval=100, idxs=None, doom=True):
        """Reindex content in Solr."""

        processed = 0
        real = timer()
        lap = timer()
        cpu = timer(clock)

        if doom:
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
                          end=-1, query=None, doom=True):
        """Reindex all cataloged content in Solr."""
        query = query or {}
        for key, value in self.request.form.items():
            if key in ['UID', 'path', 'created', 'modified', 'portal_type',
                       'object_provides', 'sort_on', 'sort_order']:
                query[key] = value
        if 'sort_on' not in query:
            query['sort_on'] = 'path'
        catalog = getToolByName(self.context, 'portal_catalog')
        items = catalog.unrestrictedSearchResults(**query)

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

        if doom:
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
        site = getSite()
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

    def diff(self):
        """Diff with portal catalog"""
        catalog = getToolByName(self.context, 'portal_catalog')
        items = catalog.unrestrictedSearchResults()
        catalog_uids = set([item.UID for item in items])
        catalog_modified = set(
            [(item.UID, solr_date(item.modified)) for item in items])

        conn = self.manager.connection
        resp = conn.search({
            u'query': u'*:*',
            u'limit': 10000000,
            u'params': {u'fl': ['UID', 'modified']},
        })
        solr_uids = set([doc['UID'].encode('utf8') for doc in resp.docs])
        solr_modified = set(
            [(doc['UID'], doc.get('modified', u'2000-01-01T00:00:00.000Z'))
             for doc in resp.docs])

        self.log('Portal Catalog contains %s items.', len(catalog_uids))
        self.log('Solr contains %s items.',  len(solr_uids))
        not_in_catalog = solr_uids - catalog_uids
        if not_in_catalog:
            self.log(
                'Items not in Portal Catalog: %s', ', '.join(not_in_catalog))
        not_in_solr = catalog_uids - solr_uids
        if not_in_solr:
            self.log('Items not in Solr: %s', ', '.join(not_in_solr))
        if not not_in_catalog and not not_in_solr:
            self.log('Solr and Portal Catalog contain the same items. :-)')
        not_in_sync = [item[0] for item in catalog_modified - solr_modified]
        if not_in_sync:
            self.log(
                'Items not in sync with catalog: %s', ', '.join(not_in_sync))
        return not_in_catalog, not_in_solr, not_in_sync

    def sync(self, commit_interval=100, idxs=None, doom=True):
        """Sync Solr with portal catalog"""
        catalog = getToolByName(self.context, 'portal_catalog')
        not_in_catalog, not_in_solr, not_in_sync = self.diff()

        if not not_in_sync and not not_in_catalog:
            return

        # (Re)index items in Solr that are not in sync
        processed = 0
        real = timer()
        lap = timer()
        cpu = timer(clock)

        if doom:
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
        self.log('Syncing Solr...')
        for uid in not_in_sync:
            catalog_item = catalog.unrestrictedSearchResults(UID=uid)[0]
            obj = catalog_item.getObject()

            handler = getMultiAdapter((obj, self.manager), ISolrIndexHandler)
            handler.add(idxs)
            processed += 1
            cpi.next()

        commit()

        # Delete items in Solr that are not in the catalog
        conn = self.manager.connection
        for uid in not_in_catalog:
            conn.delete(uid)
        conn.commit()

        self.log('Solr index synced.')
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
