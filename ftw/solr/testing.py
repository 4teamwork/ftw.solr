# -*- coding: utf-8 -*-
from ftw.solr.interfaces import PLONE51
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
import ftw.solr
import plone.app.contenttypes


class FtwSolrLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        if not PLONE51:
            import collective.indexing
            self.loadZCML(package=collective.indexing)
            z2.installProduct(app, 'collective.indexing')

        z2.installProduct(app, 'Products.DateRecurringIndex')
        self.loadZCML(package=plone.app.contenttypes)
        self.loadZCML(package=ftw.solr)
        z2.installProduct(app, 'ftw.solr')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.contenttypes:default')
        applyProfile(portal, 'ftw.solr:default')


class FtwSolrATLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        if not PLONE51:
            import collective.indexing
            self.loadZCML(package=collective.indexing)
            z2.installProduct(app, 'collective.indexing')

        self.loadZCML(package=ftw.solr)
        z2.installProduct(app, 'ftw.solr')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.solr:default')


FTW_SOLR_FIXTURE = FtwSolrLayer()
FTW_SOLR_AT_FIXTURE = FtwSolrATLayer()

FTW_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_SOLR_FIXTURE,),
    name='FtwSolrLayer:IntegrationTesting'
)

FTW_SOLR_AT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_SOLR_AT_FIXTURE,),
    name='FtwSolrATLayer:IntegrationTesting'
)

FTW_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FTW_SOLR_FIXTURE,),
    name='FtwSolrLayer:FunctionalTesting'
)
