from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest2 import TestCase


class TestReindexObjectSecurityPatches(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_CatalogAware_reindexObjectSecurity_is_patched(self):
        from Products.CMFCore.CMFCatalogAware import CatalogAware
        self.assertEquals(CatalogAware.reindexObjectSecurity.__func__.func_name,
                          'ftw_solr_CatalogAware_reindexObjectSecurity')
