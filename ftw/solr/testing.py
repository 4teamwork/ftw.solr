# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import getFSVersionTuple
from ftw.testing.layer import COMPONENT_REGISTRY_ISOLATION
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import collective.indexing
import ftw.solr
import plone.app.contenttypes


class FtwSolrLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        # import plone.app.dexterity
        # self.loadZCML(package=plone.app.dexterity)
        self.loadZCML(package=ftw.solr)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.solr:default')
        if getFSVersionTuple() >= (5, 1):
            applyProfile(portal, 'plone.app.contenttypes:default')


class FtwSolrDexterityLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        z2.installProduct(app, 'Products.DateRecurringIndex')
        self.loadZCML(package=plone.app.contenttypes)
        self.loadZCML(package=ftw.solr)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.contenttypes:default')
        applyProfile(portal, 'ftw.solr:default')


class FtwSolrCollectiveIndexingLayer(FtwSolrLayer):
    """Testing layer that loads collective.indexing's catalog patches in
    order to test behavior / functionality that depends on the integration
    via collective.indexing.
    """

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=collective.indexing)
        z2.installProduct(app, 'collective.indexing')

        self.loadZCML(package=ftw.solr)
        z2.installProduct(app, 'ftw.solr')


FTW_SOLR_FIXTURE = FtwSolrLayer()
FTW_SOLR_DEXTERITY_FIXTURE = FtwSolrDexterityLayer()
FTW_SOLR_COLLECTIVE_INDEXING_FIXTURE = FtwSolrCollectiveIndexingLayer()


FTW_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_SOLR_FIXTURE,),
    name='FtwSolrLayer:IntegrationTesting'
)

FTW_SOLR_DEXTERITY_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_SOLR_DEXTERITY_FIXTURE,),
    name='FtwSolrDexterityLayer:IntegrationTesting'
)

FTW_SOLR_COLLECTIVE_INDEXING_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_SOLR_COLLECTIVE_INDEXING_FIXTURE, COMPONENT_REGISTRY_ISOLATION),
    name='FtwSolrLayer:CollectiveIndexingIntegrationTesting'
)


FTW_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FTW_SOLR_FIXTURE,),
    name='FtwSolrLayer:FunctionalTesting'
)
