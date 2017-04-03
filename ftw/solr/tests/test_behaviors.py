from ftw.solr.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import factoriesmenu
from plone.indexer.interfaces import IIndexer
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
import transaction


def index_value_for(obj, index_name):
    catalog = getToolByName(obj, 'portal_catalog')
    indexer = getMultiAdapter((obj, catalog), IIndexer, name=index_name)
    return indexer()


def enable_behavior(behavior, type='DexterityFolder'):
    portal_types = getToolByName(getSite(), 'portal_types')
    portal_types['DexterityFolder'].behaviors.append(behavior)
    transaction.commit()


def disable_behavior(behavior, type='DexterityFolder'):
    portal_types = getToolByName(getSite(), 'portal_types')
    portal_types['DexterityFolder'].behaviors.remove(behavior)
    transaction.commit()


class TestShowInSearch(FunctionalTestCase):

    def setUp(self):
        super(TestShowInSearch, self).setUp()
        enable_behavior('ftw.solr.behaviors.IShowInSearch')

    def tearDown(self):
        super(TestShowInSearch, self).tearDown()
        disable_behavior('ftw.solr.behaviors.IShowInSearch')

    @browsing
    def test_True_by_default(self, browser):
        self.grant('Manager')
        browser.login().open()
        factoriesmenu.add('DexterityFolder')
        browser.click_on('Save')
        self.assertTrue(index_value_for(browser.context, 'showinsearch'),
                        'Expected showinsearch to be True by default.')

    @browsing
    def test_setting_to_False(self, browser):
        self.grant('Manager')
        browser.login().open()
        factoriesmenu.add('DexterityFolder')
        browser.fill({'Show in search': False}).save()
        self.assertFalse(index_value_for(browser.context, 'showinsearch'),
                         'Expected showinsearch to be set to False.')


class TestSearchwords(FunctionalTestCase):

    def setUp(self):
        super(TestSearchwords, self).setUp()
        enable_behavior('ftw.solr.behaviors.ISearchwords')

    def tearDown(self):
        super(TestSearchwords, self).tearDown()
        disable_behavior('ftw.solr.behaviors.ISearchwords')

    @browsing
    def test_searchwords_are_provided_by_indexer(self, browser):
        self.grant('Manager')
        browser.login().open()
        factoriesmenu.add('DexterityFolder')
        browser.fill({'Search words': 'Foo Bar\nBaz'}).save()
        browser.open(browser.context, view='edit')
        self.assertEquals([u'foo bar', u'baz'],
                          index_value_for(browser.context, 'searchwords'))
