# -*- coding: utf-8 -*-
from ftw.solr.contentlisting import SolrDocument
from ftw.solr.tests.utils import get_data
import json
import unittest


class TestSolrDocument(unittest.TestCase):

    def setUp(self):
        self.doc = SolrDocument(json.loads(get_data('doc.json')))

    def test_string_values_are_bytes(self):
        self.assertTrue(isinstance(self.doc.path, str))
