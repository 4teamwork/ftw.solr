# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING  # noqa
from plone import api

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that ftw.solr is properly installed."""

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']

    def test_product_installed(self):
        """Test if ftw.solr is installed."""
        if get_installer is None:
            installer = api.portal.get_tool('portal_quickinstaller')
            self.assertTrue(installer.isProductInstalled('ftw.solr'))
        else:
            installer = get_installer(self.portal, self.portal.REQUEST)
            self.assertTrue(installer.is_product_installed('ftw.solr'))

    def test_browserlayer(self):
        """Test that IFtwSolrLayer is registered."""
        from ftw.solr.interfaces import (
            IFtwSolrLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IFtwSolrLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

        if get_installer is None:
            self.installer = api.portal.get_tool('portal_quickinstaller')
            self.installer.uninstallProducts(['ftw.solr'])
        else:
            self.installer = get_installer(self.portal, self.portal.REQUEST)
            self.installer.uninstall_product('ftw.solr')

    def test_product_uninstalled(self):
        """Test if ftw.solr is cleanly uninstalled."""
        if get_installer is None:
            self.assertFalse(self.installer.isProductInstalled('ftw.solr'))
        else:
            self.assertFalse(self.installer.is_product_installed('ftw.solr'))

    def test_browserlayer_removed(self):
        """Test that IFtwSolrLayer is removed."""
        from ftw.solr.interfaces import IFtwSolrLayer
        from plone.browserlayer import utils

        self.assertNotIn(IFtwSolrLayer, utils.registered_layers())
