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
