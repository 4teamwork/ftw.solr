from collective.indexing.indexer import getOwnIndexMethod
from collective.solr.browser import maintenance
from collective.solr.browser.maintenance import checkpointIterator
from collective.solr.browser.maintenance import notimeout
from collective.solr.browser.maintenance import timer
from collective.solr.indexer import boost_values
from collective.solr.indexer import indexable
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrMaintenanceView
from collective.solr.utils import findObjects
from collective.solr.utils import prepareData
from logging import getLogger
from time import clock
from zope.component import queryUtility
from zope.interface import implements
from ftw.solr.index_processor import FtwSolrIndexProcessor


logger = getLogger('ftw.solr.maintenance')


class SolrMaintenanceView(maintenance.SolrMaintenanceView):
    """Overrides SolrMaintenanceView.reindex() so that it uses the
    FtwSolrIndexProcessor, which allows for atomic updates.
    """
    implements(ISolrMaintenanceView)

    def reindex(self, batch=1000, skip=0, idxs=[]):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """
        atomic = idxs != []
        manager = queryUtility(ISolrConnectionManager)
        proc = FtwSolrIndexProcessor(manager)
        conn = manager.getConnection()
        zodb_conn = self.context._p_jar
        log = self.mklog()
        log('reindexing solr catalog...\n')
        if skip:
            log('skipping indexing of %d object(s)...\n' % skip)
        real = timer()          # real time
        lap = timer()           # real lap time (for intermediate commits)
        cpu = timer(clock)      # cpu time
        processed = 0
        schema = manager.getSchema()
        key = schema.uniqueKey
        updates = {}            # list to hold data to be updated
        flush = lambda: conn.flush()
        flush = notimeout(flush)

        def checkPoint():
            for boost_values, data in updates.values():
                # Only update specified fields by using atomic updates
                conn.add(boost_values=boost_values, **data)
            updates.clear()
            msg = 'intermediate commit (%d items processed, ' \
                  'last batch in %s)...\n' % (processed, lap.next())
            log(msg)
            logger.info(msg)
            flush()
            zodb_conn.cacheGC()
        cpi = checkpointIterator(checkPoint, batch)
        count = 0
        for path, obj in findObjects(self.context):
            if indexable(obj):
                if getOwnIndexMethod(obj, 'indexObject') is not None:
                    log('skipping indexing of %r via private method.\n' % obj)
                    continue
                count += 1
                if count <= skip:
                    continue

                attributes = None
                if atomic:
                    attributes = idxs

                # For atomic updates to work the uniqueKey must be present
                # in *every* update operation.
                if attributes and not key in attributes:
                    attributes.append(key)

                data, missing = proc.getData(obj, attributes=attributes)
                prepareData(data)

                if not missing or atomic:
                    value = data.get(key, None)
                    if value is not None:
                        updates[value] = (boost_values(obj, data), data)
                        processed += 1
                        cpi.next()
                else:
                    log('missing data, skipping indexing of %r.\n' % obj)
        checkPoint()
        conn.commit()
        log('solr index rebuilt.\n')
        msg = 'processed %d items in %s (%s cpu time).'
        msg = msg % (processed, real.next(), cpu.next())
        log(msg)
        logger.info(msg)
