# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that ftw.solr is properly installed."""

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if ftw.solr is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'ftw.solr'))

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
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['ftw.solr'])

    def test_product_uninstalled(self):
        """Test if ftw.solr is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'ftw.solr'))

    def test_browserlayer_removed(self):
        """Test that IFtwSolrLayer is removed."""
        from ftw.solr.interfaces import \
            IFtwSolrLayer
        from plone.browserlayer import utils
        self.assertNotIn(
           IFtwSolrLayer,
           utils.registered_layers())
