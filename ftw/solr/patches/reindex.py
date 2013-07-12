from Acquisition import aq_base
from collective.indexing.queue import getQueue
from collective.indexing.queue import processQueue
from logging import WARNING
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.log import log
from Products.Archetypes.utils import isFactoryContained
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.utils import getToolByName
import logging


logger = logging.getLogger('ftw.solr')


def ftw_solr_CatalogMultiplex_reindexObjectSecurity(self, skip_self=False):
    """update security information in all registered catalogs.
    """
    if isFactoryContained(self):
        return
    at = getToolByName(self, TOOL_NAME, None)
    if at is None:
        return

    catalogs = [c for c in at.getCatalogsByType(self.meta_type)
                           if ICatalogTool.providedBy(c)]

    # Account for name mangling of double underscore attributes
    path = self._CatalogMultiplex__url()

    for catalog in catalogs:
        for brain in catalog.unrestrictedSearchResults(path=path):
            brain_path = brain.getPath()
            if brain_path == path and skip_self:
                continue

            # Get the object
            if hasattr(aq_base(brain), '_unrestrictedGetObject'):
                ob = brain._unrestrictedGetObject()
            else:
                # BBB: Zope 2.7
                ob = self.unrestrictedTraverse(brain_path, None)
            if ob is None:
                # BBB: Ignore old references to deleted objects.
                # Can happen only in Zope 2.7, or when using
                # catalog-getObject-raises off in Zope 2.8
                log("reindexObjectSecurity: Cannot get %s from catalog" %
                    brain_path, level=WARNING)
                continue

            # Also update relevant security indexes in solr
            indexer = getQueue()
            indexer.reindex(ob, self._cmf_security_indexes)


def ftw_solr_CatalogAware_reindexObjectSecurity(self, skip_self=False):
    """ Reindex security-related indexes on the object.
    """
    catalog = self._getCatalogTool()
    if catalog is None:
        return
    path = '/'.join(self.getPhysicalPath())

    # XXX if _getCatalogTool() is overriden we will have to change
    # this method for the sub-objects.
    for brain in catalog.unrestrictedSearchResults(path=path):
        brain_path = brain.getPath()
        if brain_path == path and skip_self:
            continue
        # Get the object
        ob = brain._unrestrictedGetObject()
        if ob is None:
            # BBB: Ignore old references to deleted objects.
            # Can happen only when using
            # catalog-getObject-raises off in Zope 2.8
            logger.warning("reindexObjectSecurity: Cannot get %s from "
                           "catalog", brain_path)
            continue
        # Recatalog with the same catalog uid.
        s = getattr(ob, '_p_changed', 0)

        # Also update relevant security indexes in solr
        indexer = getQueue()
        indexer.reindex(ob, self._cmf_security_indexes)

        if s is None: ob._p_deactivate()

