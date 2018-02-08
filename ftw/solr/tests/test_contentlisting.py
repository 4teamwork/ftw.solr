# -*- coding: utf-8 -*-
from DateTime import DateTime
from ftw.solr.connection import SolrResponse
from ftw.solr.contentlisting import SolrContentListing
from ftw.solr.contentlisting import SolrContentListingObject
from ftw.solr.contentlisting import SolrDocument
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING
from ftw.solr.tests.utils import get_data
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import json
import unittest


class TestContentListing(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.resp = SolrResponse(body=get_data('search.json'), status=200)
        self.contentlisting = SolrContentListing(self.resp)

    def test_contentlisting_creation(self):
        contentlisting = IContentListing(self.resp)
        self.assertTrue(isinstance(contentlisting, SolrContentListing))

    def test_contentlisting_actual_result_count(self):
        self.assertEqual(self.contentlisting.actual_result_count, 3)

    def test_contentlisting_getitem(self):
        self.assertTrue(
            IContentListingObject.providedBy(self.contentlisting[0]))

    def test_contentlisting_iteration(self):
        self.assertTrue(IContentListingObject.providedBy(
            [item for item in self.contentlisting][0]))


class TestContentListingObject(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.obj = SolrContentListingObject(SolrDocument(
            json.loads(get_data('doc.json'))))

    def test_idublincore_title(self):
        self.assertEqual(self.obj.Title(), 'My Document')

    def test_idublincore_description(self):
        self.assertEqual(self.obj.Description(), 'Foo bar baz.')

    def test_idublincore_type(self):
        self.assertEqual(self.obj.Type(), 'Document')

    def test_idublincore_created(self):
        self.assertEqual(
            self.obj.created(), DateTime('2017/08/01 13:17:0.009000 GMT+2'))

    def test_idublincore_modified(self):
        self.assertEqual(
            self.obj.modified(), DateTime('2017/12/31 12:17:0.137000 GMT+1'))

    def test_idublincore_effective(self):
        self.assertEqual(
            self.obj.effective(), None)

    def test_idublincore_expires(self):
        self.assertEqual(
            self.obj.expires(), None)

    def test_idublincore_creationdate(self):
        self.assertEqual(
            self.obj.CreationDate(), '2017-08-01T13:17:00+02:00')

    def test_idublincore_modificationdate(self):
        self.assertEqual(
            self.obj.ModificationDate(), '2017-12-31T12:17:00+01:00')

    def test_idublincore_effectivedate(self):
        self.assertEqual(
            self.obj.EffectiveDate(), None)

    def test_idublincore_expirationdate(self):
        self.assertEqual(
            self.obj.ExpirationDate(), None)

    def test_icontentlistingobject_getid(self):
        self.assertEqual(self.obj.getId(), 'my-document.docx')

    def test_icontentlistingobject_getobject(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('Document', 'my-document')
        obj = portal['my-document']
        self.obj.doc.data[u'path'] = '/'.join(obj.getPhysicalPath())
        self.assertEqual(self.obj.getObject(), obj)

    def test_icontentlistingobject_getobject_for_not_existing_object(self):
        self.assertEqual(self.obj.getObject(), None)

    def test_icontentlistingobject_getdataorigin(self):
        self.assertTrue(isinstance(self.obj.getDataOrigin(), SolrDocument))

    def test_icontentlistingobject_getpath(self):
        self.assertEqual(
            self.obj.getPath(), '/plone/my-folder-1/my-document.docx')

    def test_icontentlistingobject_geturl(self):
        self.assertEqual(
            self.obj.getURL(),
            'http://nohost/plone/my-folder-1/my-document.docx')

    def test_icontentlistingobject_uuid(self):
        self.assertEqual(
            self.obj.uuid(), '9398dad21bcd49f8a197cd50d10ea778')

    def test_icontentlistingobject_geticon(self):
        self.assertEqual(
            self.obj.getIcon(),
            '<img width="16" height="16" '
            'src="http://nohost/plone/icon_dokument_word.gif" '
            'alt="Page Word 2007 document" />')

    def test_icontentlistingobject_getsize(self):
        self.assertEqual(self.obj.getSize(), '374 KB')

    def test_icontentlistingobject_review_state(self):
        self.assertEqual(self.obj.review_state(), 'private')

    def test_icontentlistingobject_portaltype(self):
        self.assertEqual(self.obj.PortalType(), 'Document')

    def test_icontentlistingobject_croppeddescription(self):
        self.assertEqual(self.obj.CroppedDescription(), 'Foo bar baz.')

    def test_icontentlistingobject_contenttypeclass(self):
        self.assertEqual(self.obj.ContentTypeClass(), 'contenttype-document')
