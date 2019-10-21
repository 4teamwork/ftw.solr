from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.solr import IS_PLONE_5
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.dexterity.fti import DexterityFTI
from plone.testing import z2
from zope.configuration import xmlconfig
import ftw.solr.tests.builders


class SolrLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        import z3c.autoinclude
        xmlconfig.file('meta.zcml', z3c.autoinclude,
                       context=configurationContext)

        if IS_PLONE_5:

            xmlconfig.string(
                '<configure xmlns="http://namespaces.zope.org/zope">'
                '  <includePlugins package="plone" />'
                '  <includePluginsOverrides package="plone" />'
                '  <include package="collective.dexteritytextindexer" />'
                '</configure>',
                context=configurationContext)

        else:
            xmlconfig.string(
                '<configure xmlns="http://namespaces.zope.org/zope">'
                '  <includePlugins package="plone" />'
                '  <includePluginsOverrides package="plone" />'
                '  <include package="collective.indexing" />'
                '  <include package="collective.dexteritytextindexer" />'
                '</configure>',
                context=configurationContext)

            z2.installProduct(app, 'collective.indexing')
            z2.installProduct(app, 'Products.DateRecurringIndex')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.dexterity:default')


        applyProfile(portal, 'plone.app.contenttypes:default')

        applyProfile(portal, 'ftw.solr:default')

        fti = DexterityFTI('DexterityFolder',
                           klass="plone.dexterity.content.Container",
                           global_allow=True)
        portal.portal_types._setObject('DexterityFolder', fti)
        fti.lookupSchema()


SOLR_FIXTURE = SolrLayer()
SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(SOLR_FIXTURE, ), name="ftw.solr:integration")
SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(SOLR_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.solr:functional")
