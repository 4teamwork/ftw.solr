# -*- coding: utf-8 -*-
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer

import ftw.solr


class FtwSolrLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity
        self.loadZCML(package=plone.app.dexterity)
        self.loadZCML(package=ftw.solr)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.solr:default')


FTW_SOLR_FIXTURE = FtwSolrLayer()


FTW_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FTW_SOLR_FIXTURE,),
    name='FtwSolrLayer:IntegrationTesting'
)


FTW_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FTW_SOLR_FIXTURE,),
    name='FtwSolrLayer:FunctionalTesting'
)
