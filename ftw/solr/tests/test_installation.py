from Products.CMFCore.utils import getToolByName
from ftw.solr.interfaces import IFtwSolrLayer
from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from plone.browserlayer.utils import registered_layers
from unittest2 import TestCase


class TestInstallation(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_ftw_solr_profile_installed(self):
        portal = self.layer['portal']
        portal_setup = getToolByName(portal, 'portal_setup')

        version = portal_setup.getLastVersionForProfile(
            'ftw.solr:default')
        self.assertNotEqual(version, None)
        self.assertNotEqual(version, 'unknown')

    def test_collective_solr_profile_installed(self):
        portal = self.layer['portal']
        portal_setup = getToolByName(portal, 'portal_setup')

        version = portal_setup.getLastVersionForProfile(
            'collective.solr:default')
        self.assertNotEqual(version, None)
        self.assertNotEqual(version, 'unknown')

    def test_request_layer_active(self):
        layers = registered_layers()
        self.assertIn(IFtwSolrLayer, layers)
