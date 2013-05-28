from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest2 import TestCase
from plone.indexer.wrapper import IndexableObjectWrapper


class TestSnippetText(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def test_id_not_in_snippet_text(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1',
                                          title=u"Document 1")]
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertNotIn('doc1', wrapped.snippetText)

    def test_title_not_in_snippet_text(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1',
                                          title=u"Document 1")]
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertNotIn('Document 1', wrapped.snippetText)

    def test_searchwords_not_in_snippet_text(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1',
                                          title=u"Document 1",
                                          searchwords=u"Spam\nEggs")]
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertNotIn('Spam', wrapped.snippetText)
        self.assertNotIn('Eggs', wrapped.snippetText)

    def test_body_text_in_snippet_text(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1',
                                          title=u"Document 1",
                                          text=u"Body Text")]
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertIn('Body Text', wrapped.snippetText)

    def test_description_in_snippet_text(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1',
                                          title=u"Document 1",
                                          description=u"Description for "
                                                       "Document 1")]
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertIn('Description for Document 1', wrapped.snippetText)

    def test_strip_html_tags(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1')]
        def SearchableText(self):
            return "<p>Body Text</p>"
        doc.SearchableText = SearchableText.__get__(doc, doc.__class__) 
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertIn('Body Text', wrapped.snippetText)
        self.assertNotIn('<p>', wrapped.snippetText)
        self.assertNotIn('</p>', wrapped.snippetText)

    def test_searchable_text_indexer(self):
        from plone.indexer.interfaces import IIndexer
        from Products.ZCatalog.interfaces import IZCatalog
        from zope.interface import implements, Interface, alsoProvides
        from zope.component import provideAdapter, adapts
        class IMarker(Interface):
            pass
        class SearchableText(object):
            implements(IIndexer)
            adapts(IMarker, IZCatalog)
            def __init__(self, context, catalog):
                pass
            def __call__(self):
                return "Spam and eggs"
        provideAdapter(SearchableText, name="SearchableText")

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1')]
        alsoProvides(doc, IMarker)
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertIn('Spam and eggs', wrapped.snippetText)

    def test_non_archetypes_content(self):
        from Products.CMFCore.interfaces import IContentish
        from zope.interface import implements
        class DummyType(object):
            implements(IContentish)
            def SearchableText(self_):
                return "Dummy SearchableText"
            def Title(self_):
                return "Dummy"
            def Schema(self_):
                self.fail("Not an archetypes object.")
        portal = self.layer['portal']
        doc = DummyType()
        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertEquals(" SearchableText", wrapped.snippetText)
