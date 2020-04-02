from datetime import date
from DateTime import DateTime
from datetime import datetime
from ftw.solr.browser.maintenance import checkpoint_iterator
from ftw.solr.browser.maintenance import timer
from ftw.solr.converters import to_iso8601
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrIndexHandler
from ftw.solr.interfaces import ISolrSettings
from ftw.upgrade import UpgradeStep
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from time import clock
from zope.component import getMultiAdapter
from zope.component import queryUtility
import logging


def _pre_datetime_format_fix_to_iso8601(value, multivalued=False):
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = u'%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (
            v.year(), v.month(), v.day(), v.hour(), v.minute(), v.second()
        )
    elif isinstance(value, datetime):
        if value.tzinfo is not None:
            # Convert to timezone naive in UTC
            value = (value - value.utcoffset()).replace(tzinfo=None)

        value = u'%04d-%02d-%02dT%02d:%02d:%02d.%03dZ' % (
            value.year, value.month, value.day, value.hour, value.minute,
            value.second, value.microsecond / 1000
        )
    elif isinstance(value, date):
        value = u'%04d-%02d-%02dT%02d:%02d:%02d.%03dZ' % (
            value.year, value.month, value.day, 0, 0, 0, 0
        )
    else:
        value = None
    return value


def _solr_date(date):
    """Solr date representation. Fractional seconds are stripped if 0."""
    value = to_iso8601(date)
    if value.endswith('.000Z'):
        value = value[:-5] + 'Z'
    return value


def _pre_datetime_format_fix_solr_date(date):
    """Solr date representation. Fractional seconds are stripped if 0."""
    value = _pre_datetime_format_fix_to_iso8601(date)
    if value.endswith('.000Z'):
        value = value[:-5] + 'Z'
    return value


commit_interval = 100


class UpdateModifiedIndex(UpgradeStep):
    """Update modified index.
    """

    deferrable = True

    def __call__(self):
        self.logger = logging.getLogger('ftw.upgrade')

        if not self.is_enabled():
            self.log("Skipping: Solr is not enabled.")
            return
        self.sync()

    def is_enabled(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(ISolrSettings)
        return settings.enabled

    def get_objects_that_need_syncing_of_modified(self):
        """Find objects that are not in sync only due to change in DateTime
        rounding"""

        catalog = getToolByName(self.portal, 'portal_catalog')
        items = catalog.unrestrictedSearchResults()
        catalog_modified = set(
            [(item.UID, _solr_date(item.modified)) for item in items])
        pre_datetime_format_fix_catalog_modified = set(
            [(item.UID, _pre_datetime_format_fix_solr_date(item.modified)) for item in items])

        conn = self.manager.connection
        resp = conn.search({
            u'query': u'*:*',
            u'limit': 10000000,
            u'params': {u'fl': ['UID', 'modified']},
        })
        solr_modified = set(
            [(doc['UID'], doc.get('modified', u'2000-01-01T00:00:00.000Z'))
             for doc in resp.docs])

        not_in_sync = set(
            (item[0] for item in catalog_modified - solr_modified))
        pre_datetime_format_fix_not_in_sync = set(
            (item[0] for item in pre_datetime_format_fix_catalog_modified - solr_modified))

        # We only want to reindex modified for objects that would
        # be in sync if we hadn't modified the rounding in solr_date
        to_correct = not_in_sync - pre_datetime_format_fix_not_in_sync
        return to_correct

    def sync(self, commit_interval=100, idxs=None):
        """Sync Solr with portal catalog"""
        if not self.is_enabled():
            return 'Solr indexing is disabled.'

        to_correct = self.get_objects_that_need_syncing_of_modified()

        # Reindex modified for Solr items that should be in sync
        processed = 0
        real = timer()
        lap = timer()
        cpu = timer(clock)

        def commit():
            conn = self.manager.connection
            conn.commit(soft_commit=False, extract_after_commit=False)
            self.log(
                'Intermediate commit (%d items processed, last batch in %s)',
                processed, next(lap))

        cpi = checkpoint_iterator(commit, interval=commit_interval)
        self.log('Syncing modified to solr for {} objects'.format(len(to_correct)))
        catalog = getToolByName(self.portal, 'portal_catalog')
        for uid in to_correct:
            catalog_item = catalog.unrestrictedSearchResults(UID=uid)[0]

            handler = getMultiAdapter((catalog_item, self.manager), ISolrIndexHandler)
            handler.add(['modified'])
            processed += 1
            next(cpi)

        commit()

        conn = self.manager.connection
        conn.commit(soft_commit=False)

        self.log('Solr modified index synced.')
        self.log(
            'Processed %d items in %s (%s cpu time).',
            processed, next(real), next(cpu))

    @property
    def manager(self):
        return queryUtility(ISolrConnectionManager)

    def log(self, msg, *args):
        self.logger.info(msg, *args)
