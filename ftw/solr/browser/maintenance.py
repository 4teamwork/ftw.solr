# -*- coding: utf-8 -*-
from App.config import getConfiguration
from ftw.solr.converters import to_iso8601
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexHandler
from ftw.solr.interfaces import ISolrSettings
from itertools import islice
from logging import getLogger
from os.path import dirname
from os.path import join as pjoin
from plone.registry.interfaces import IRegistry
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
from logging.handlers import TimedRotatingFileHandler
import transaction


logger = getLogger('ftw.solr.maintenance')
logger.setLevel(logging.DEBUG)


def get_logfile_path():
    """Determine the path for solr-maintenance.log.
    This will be derived from Zope2's EventLog location, in order to not
    have to figure out the path to var/log/ and the instance name ourselves.
    """
    zconf = getConfiguration()
    eventlog = getattr(zconf, 'eventlog', None)
    if eventlog is None:
        return None

    handler_factories = eventlog.handler_factories
    eventlog_path = handler_factories[0].section.path
    logdir = dirname(eventlog_path)
    return pjoin(logdir, 'solr-maintenance.log')


def setup_maintenance_loghandler():
    logfile_path = get_logfile_path()
    if not logfile_path:
        return

    handler = TimedRotatingFileHandler(
        logfile_path,
        when='midnight', backupCount=7)
    handler.setLevel(logging.DEBUG)
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)


setup_maintenance_loghandler()


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


def ellipsified_join(items, max):
    if max is not None:
        items_to_join = list(islice(items, max))
        if len(items) > max:
            items_to_join.append('...')
    else:
        items_to_join = items
    return ', '.join(items_to_join)


class SolrMaintenanceView(BrowserView):
    """Helper view for indexing content in Solr."""

    def __init__(self, context, request):
        super(SolrMaintenanceView, self).__init__(context, request)
        self.request.RESPONSE.setHeader('Content-Type', 'text/plain')

    def is_enabled(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(ISolrSettings)
        return settings.enabled

    def optimize(self):
        """Optimize the Solr index."""
        if not self.is_enabled():
            return 'Solr indexing is disabled.'
        conn = self.manager.connection
        conn.optimize()
        return 'Solr index optimized.'

    def clear(self):
        """Clear all data from Solr index."""
        if not self.is_enabled():
            return 'Solr indexing is disabled.'
        conn = self.manager.connection
        conn.delete_by_query('*:*')
        conn.commit(soft_commit=False)
        return 'Solr index cleared.'

    def reindex(self, commit_interval=100, idxs=None, doom=True):
        """Reindex content in Solr."""
        if not self.is_enabled():
            return 'Solr indexing is disabled.'

        processed = 0
        real = timer()
        lap = timer()
        cpu = timer(clock)

        if doom:
            transaction.doom()

        zodb_conn = self.context._p_jar

        def commit():
            conn = self.manager.connection
            conn.commit(soft_commit=False, extract_after_commit=False)
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
        if not self.is_enabled():
            return 'Solr indexing is disabled.'

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
            conn.commit(soft_commit=False, extract_after_commit=False)
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

    def diff(self, max_diff=5):
        """Diff with portal catalog"""
        if not self.is_enabled():
            return 'Solr indexing is disabled.'

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
        self.log('Solr contains %s items.', len(solr_uids))
        not_in_catalog = solr_uids - catalog_uids
        if not_in_catalog:
            self.log(
                'Total of %s items not in Portal Catalog: %s',
                len(not_in_catalog),
                ellipsified_join(not_in_catalog, max_diff))
        not_in_solr = catalog_uids - solr_uids
        if not_in_solr:
            self.log(
                'Total of %s items not in Solr: %s',
                len(not_in_solr),
                ellipsified_join(not_in_solr, max_diff))
        if not not_in_catalog and not not_in_solr:
            self.log('Solr and Portal Catalog contain the same items. :-)')

        not_in_sync = [item[0] for item in catalog_modified - solr_modified]
        incomplete = conn.search({
            u'query': u'-created:[* TO *]',
            u'limit': 10000000,
            u'params': {u'fl': 'UID'},
        })
        not_in_sync.extend([doc['UID'] for doc in incomplete.docs])
        if not_in_sync:
            self.log(
                'Total of %s items not in sync: %s',
                len(not_in_sync),
                ellipsified_join(not_in_sync, max_diff))
        return not_in_catalog, not_in_solr, not_in_sync

    def sync(self, commit_interval=100, idxs=None, doom=True, max_diff=5):
        """Sync Solr with portal catalog"""
        if not self.is_enabled():
            return 'Solr indexing is disabled.'

        catalog = getToolByName(self.context, 'portal_catalog')
        not_in_catalog, not_in_solr, not_in_sync = self.diff(max_diff=max_diff)

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
            conn.commit(soft_commit=False, extract_after_commit=False)
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
        conn.commit(soft_commit=False)

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
