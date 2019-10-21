from plone.indexer.interfaces import IIndexer
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.utils import isFactoryContained
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces._content import ICatalogAware
from Products.CMFCore.utils import getToolByName
from zope.component import queryMultiAdapter
import logging


logger = logging.getLogger('ftw.solr')


def is_index_value_equal(old, new):
    """Compares an old and a new index value.
    If the value is of type list, it is compared as set since this usually is
    used in a KeywordIndex, where the order is not relevant.
    """
    if type(old) != type(new):
        return False
    if isinstance(old, list):
        return set(old) == set(new)
    return old == new


def is_index_up_to_date(catalog, obj, index_name):
    """Checks, whether the passed index (`index_name`) of the passed object (`obj`)
    is up to date on the passed catalog (`catalog`).
    """

    indexer = queryMultiAdapter((obj, catalog), IIndexer, name=index_name)
    if indexer is None:
        indexer = getattr(obj, index_name, None)

    if indexer is None:
        # We cannot re-generate the index data, therfore we
        # act as if it is outdated
        return False

    else:
        path = '/'.join(obj.getPhysicalPath())
        rid = catalog.getrid(path)
        if rid is None:
            # the object was not yet indexed
            return False

        indexed_values = catalog.getIndexDataForRID(catalog.getrid(path))
        value_before = indexed_values.get(index_name, None)
        value_after = indexer()
        if not is_index_value_equal(value_before, value_after):
            return False

    return True


def recursive_index_security(catalog, obj):
    """This function reindexes the security indexes for an object in a specific catalog
    recursively.
    It does this by walking down the tree and checking on every object whether a
    the security indexes are already up to date.
    If the security indexes are already up to date, it stops walking down the tree.

    The aim of stopping to walk down is to improve the performance drastically on
    large trees.
    The expectation is that if a children is up to date but the parent wasnt, the
    reason is usally that the children does not inherit the relevant values (for
    example it does not inherit the View permission) and thus the grand-children will
    also not change, so we can abort wakling down the path.
    """
    indexes_to_update = []

    # Since objectValues returns all objects, including placefulworkflow policy
    # objects, we have to check if the object is Catalog aware.
    if not ICatalogAware.providedBy(obj):
        return

    for index_name in obj._cmf_security_indexes:
        if not is_index_up_to_date(catalog, obj, index_name):
            indexes_to_update.append(index_name)

    if len(indexes_to_update) > 0:
        obj.reindexObject(idxs=indexes_to_update)

        # We assume that if the parent is up to date, all children are too.
        # This basically only walks into the tree untill an object is up to date -
        # usually because it does not inherit the security relevant thigns - and then
        # stops.
        for subobj in obj.objectValues():
            recursive_index_security(catalog, subobj)

def ftw_solr_CatalogAware_reindexObjectSecurity(self, skip_self=False):
    """ Reindex security-related indexes on the object.
    """
    catalog = self._getCatalogTool()
    if catalog is None:
        return

    s = getattr(self, '_p_changed', 0)
    recursive_index_security(catalog, self)
    if s is None:
        self._p_deactivate()
