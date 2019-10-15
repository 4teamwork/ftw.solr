from collective.dexteritytextindexer.utils import searchable
from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from ftw.solr.tests.utils import enable_textindexer_behavior
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield import RichTextValue
from plone.indexer.wrapper import IndexableObjectWrapper
from unittest2 import TestCase


class TestSnippetText(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        super(TestSnippetText, self).setUp()
        enable_textindexer_behavior('Document')
        searchable(IRichText, 'text')

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
                                          text=RichTextValue(u"Body Text"))]
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
        doc = portal[portal.invokeFactory('Document', 'doc1',
                                          title=u"Document 1",
                                          text=RichTextValue(u"<p>Body Text</p>"))]

        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertIn('Body Text', wrapped.snippetText)
        self.assertNotIn('<p>', wrapped.snippetText)
        self.assertNotIn('</p>', wrapped.snippetText)

    def test_searchable_text_indexer(self):
        from collective import dexteritytextindexer
        from zope.component import adapts
        from zope.component import provideAdapter
        from zope.interface import implements

        class CustomSearchableTextExtender(object):
            adapts(IRichText)
            implements(dexteritytextindexer.IDynamicTextIndexExtender)

            def __init__(self, context):
                self.context = context

            def __call__(self):
                return 'Additional infos'

        provideAdapter(CustomSearchableTextExtender, name="IRichText")

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        doc = portal[portal.invokeFactory('Document', 'doc1')]

        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertIn('Additional infos', wrapped.snippetText)

    def test_searchwords_are_index_lowered(self):
        from Products.CMFCore.interfaces import IContentish
        from zope.interface import implements
        from ftw.solr.behaviors import ISearchwords

        class DummyType(object):
            implements(IContentish, ISearchwords)

            def SearchableText(self_):
                return "Dummy SearchableText"

            def Title(self_):
                return "Dummy"

            @property
            def searchwords(self_):
                return u"Spam\nEggs"

            def Schema(self_):
                self.fail("Not an archetypes object.")

        portal = self.layer['portal']
        doc = DummyType()

        wrapped = IndexableObjectWrapper(doc, portal.portal_catalog)
        self.assertEquals([u'spam', u'eggs'], wrapped.searchwords)
