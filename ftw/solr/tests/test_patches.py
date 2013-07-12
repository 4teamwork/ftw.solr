from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest2 import TestCase


class TestReindexObjectSecurityPatches(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_CatalogMultiplex_reindexObjectSecurity_is_patched(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Test base class CatalogMultiplex is patched
        from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
        self.assertEquals(CatalogMultiplex.reindexObjectSecurity.__func__.func_name,
                          'ftw_solr_CatalogMultiplex_reindexObjectSecurity')

        # Test actual objects inheriting from CatalogMultiplex are patched
        doc = portal[portal.invokeFactory('Document', 'doc1', title=u"Doc1")]
        self.assertEquals(doc.reindexObjectSecurity.__func__.func_name,
                          'ftw_solr_CatalogMultiplex_reindexObjectSecurity')

    def test_CatalogAware_reindexObjectSecurity_is_patched(self):
        from Products.CMFCore.CMFCatalogAware import CatalogAware
        self.assertEquals(CatalogAware.reindexObjectSecurity.__func__.func_name,
                          'ftw_solr_CatalogAware_reindexObjectSecurity')
