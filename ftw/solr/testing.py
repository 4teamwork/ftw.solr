from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.testing import z2
from zope.configuration import xmlconfig


class SolrLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        import z3c.autoinclude
        xmlconfig.file('meta.zcml', z3c.autoinclude,
                       context=configurationContext)
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '  <include package="collective.indexing" />'
            '</configure>',
            context=configurationContext)

        z2.installProduct(app, 'collective.indexing')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.solr:default')


SOLR_FIXTURE = SolrLayer()
SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(SOLR_FIXTURE, ), name="ftw.solr:integration")
SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(SOLR_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.solr:functional")
