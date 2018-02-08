# -*- coding: utf-8 -*-
from ftw.solr.contentlisting import SolrDocument
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING
from ftw.solr.tests.utils import get_data
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
import json
import unittest


class TestSolrDocument(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.doc = SolrDocument(json.loads(get_data('doc.json')))

    def test_string_values_are_bytes(self):
        self.assertTrue(isinstance(self.doc.path, str))
        self.assertTrue(isinstance(self.doc.allowedRolesAndUsers[0], str))

    def test_getpath(self):
        self.assertEqual(
            self.doc.getPath(), '/plone/my-folder-1/my-document.docx')

    def test_geturl(self):
        self.assertEqual(
            self.doc.getURL(),
            'http://nohost/plone/my-folder-1/my-document.docx')

    def test_get_relative_url(self):
        self.assertEqual(
            self.doc.getURL(relative=True),
            '/plone/my-folder-1/my-document.docx')

    def test_getobject(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('Document', 'my-document.docx')
        obj = portal['my-document.docx']
        self.doc.data[u'path'] = '/'.join(obj.getPhysicalPath())
        self.assertEqual(self.doc.getObject(), obj)

    def test_getobject_for_not_existing_object(self):
        self.assertEqual(self.doc.getObject(), None)

    def test_getobject_for_acquired_object_at_wrong_path(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('Document', 'my-document.docx')
        portal.invokeFactory('Folder', 'my-folder-1')
        self.assertEqual(self.doc.getObject(), None)
