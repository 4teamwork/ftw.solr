from ftw.solr.interfaces import PLONE51
from plone.indexer.interfaces import IIndexer
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.utils import isFactoryContained
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces._content import ICatalogAware
from Products.CMFCore.utils import getToolByName
from zope.component import queryMultiAdapter

if not PLONE51:
    # Make sure collective.indexing patches are applied before our patches
    import collective.indexing.monkey  # noqa


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
    """Checks whether the passed index (`index_name`) of the passed object
    (`obj`) is up to date in the passed catalog (`catalog`).
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

        if any(r in value_after for r in ('Anonymous', 'Authenticated')):
            # Account for the shortcut in the allowedRolesAndUsers indexer
            # regarding these system roles:
            #
            # If any of these roles are present in the allowed roles, the
            # resulting value to be indexed gets simplified to just that
            # role name.
            #
            # This can lead to situations where the effective set of allowed
            # roles and principals changed, but the indexed value stays the
            # same. That's fine for that specific object, but the change may
            # make it necessary to reindex security for a child further down
            # the line.
            #
            # But because we use is_index_up_to_date() to determine
            # when to stop recursion, we would stop recursion too early in
            # that case.
            #
            # We therefore always assume the indexed value has changed if we
            # see any of these two roles in the new indexed value.
            return False

        if not is_index_value_equal(value_before, value_after):
            return False

    return True


def recursive_index_security(catalog, obj, skip_self=False):
    """This function recursively reindexes the security indexes for an object
    in a specific catalog.

    It does so by walking down the tree and checking for every object whether
    its security indexes are already up to date. If they are up to date, it
    stops recursion.

    The aim of terminating recursion early is to drastically improve
    performance for large trees. This also avoids unnecessarily reindexing the
    same objects multiple times if this function is called for several
    overlapping subtrees.

    Reasoning why terminating recursion early is safe:
    --------------------------------------------------

    CMFCatalogAware.reindexObjectSecurity() needs to be recursive because
    changes to an object's security may affect contained subobjects.

    Indexed security for objects in Plone can only be influenced by their
    parents via some kind of inheritance. There's exactly two inheritance
    mechanisms in play:

    - Acquisition of permissions via the obj's security settings (manage_access)
    - Inheritance of local roles

    (An obj's security settings can indirectly be managed via workflows. This
    doesn't matter here though, it's irrelevant how exactly they came to be).

    In both of these cases, only the immediate parent of a subobject is
    relevant for inheritance. Therefore, if an objects indexed security didn't
    experience any changes, neither can any of its subobjects - recursively.

    Because of this, downstream propagation can be stopped as soon as an
    object is encountered whose indexed security didn't change.

    (Note: This assumes that the indexed allowed roles of an object correspond
    exactly to the real allowed roles - if the real roles change, so does the
    indexed value. This isn't strictly the case - we take care of that in
    is_index_up_to_date(), see the corresponding comment there.)

    ---

    In the case of workflow changes, reindexObjectSecurity() still needs to
    be called for every object that is *directly* affected by the change:

    - switched to a different WF
    - to a different WF state
    - changes in the WF state's security settings
    - object moved to/out of a placeful WF).

    Identifying these objects is usually easy, and you can't and must not rely
    on reinexObjectSecurity's recursion to pick them up. Instead, they can be
    determined by querying for the relevant criteria, e.g. objects that have
    a particular WF.

    Recursion will then take care of updating security indexes for affected
    subobjects that *don't* meet the criteria for being directly affected (
    like subobjects with a different workflow).
    """
    indexes_to_update = []

    # Since objectValues returns all objects, including placefulworkflow policy
    # objects, we have to check if the object is Catalog aware.
    if not ICatalogAware.providedBy(obj):
        return

    for index_name in obj._cmf_security_indexes:
        if not is_index_up_to_date(catalog, obj, index_name):
            indexes_to_update.append(index_name)

    if indexes_to_update:
        if not skip_self:
            obj.reindexObject(idxs=indexes_to_update)

        # We assume that if the parent is up to date, all children are too.
        # Therefore we stop recursion as soon as we encounter an object
        # whose security indexes are up to date.
        for subobj in obj.objectValues():
            recursive_index_security(catalog, subobj)


def ftw_solr_CatalogMultiplex_reindexObjectSecurity(self, skip_self=False):
    """Update security information in all registered catalogs.
    """
    if isFactoryContained(self):
        return
    at = getToolByName(self, TOOL_NAME, None)
    if at is None:
        return

    catalogs = [c for c in at.getCatalogsByType(self.meta_type)
                if ICatalogTool.providedBy(c)]

    for catalog in catalogs:
        recursive_index_security(catalog, self, skip_self=skip_self)


def ftw_solr_CatalogAware_reindexObjectSecurity(self, skip_self=False):
    """Reindex security-related indexes on the object.
    """
    catalog = self._getCatalogTool()
    if catalog is None:
        return

    s = getattr(self, '_p_changed', 0)
    recursive_index_security(catalog, self, skip_self=skip_self)
    if s is None:
        self._p_deactivate()


CMFCatalogAware.reindexObjectSecurity = ftw_solr_CatalogAware_reindexObjectSecurity  # noqa
CatalogMultiplex.reindexObjectSecurity = ftw_solr_CatalogMultiplex_reindexObjectSecurity  # noqa
