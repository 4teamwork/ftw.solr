from ftw.solr.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import factoriesmenu
from plone.indexer.interfaces import IIndexer
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
import transaction


def index_value_for(obj, index_name):
    catalog = getToolByName(obj, 'portal_catalog')
    indexer = getMultiAdapter((obj, catalog), IIndexer, name=index_name)
    return indexer()


class TestShowInSearch(FunctionalTestCase):

    def setUp(self):
        super(TestShowInSearch, self).setUp()
        portal_types = getToolByName(self.portal, 'portal_types')
        portal_types['DexterityFolder'].behaviors += (
            'ftw.solr.behaviors.IShowInSearch', )
        transaction.commit()

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
