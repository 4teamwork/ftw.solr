from ftw.solr.connection import SolrResponse
from ftw.solr.tests.utils import get_data
import socket
import unittest


class TestResponse(unittest.TestCase):

    def test_response_from_exception(self):
        exception = socket.error(61, 'Connection refused')
        resp = SolrResponse(exception=exception)
        self.assertFalse(resp.is_ok())
        self.assertEqual(resp.exception, exception)

    def test_response_from_bad_body(self):
        resp = SolrResponse(body='bad', status=200)
        self.assertFalse(resp.is_ok())
        self.assertEqual(resp.status, -1)

    def test_response_from_bad_request(self):
        body = get_data('bad_request.json')
        resp = SolrResponse(body=body, status=400)
        self.assertFalse(resp.is_ok())
        self.assertEqual(resp.http_status, 400)
        self.assertEqual(resp.status, 400)
        self.assertEqual(resp[u'error'][u'code'], 400)

    def test_response_from_search_request(self):
        body = get_data('search.json')
        resp = SolrResponse(body=body, status=200)
        self.assertTrue(resp.is_ok())
        self.assertEqual(len(resp.docs), 3)
        self.assertEqual(resp.num_found, 3)
        self.assertEqual(resp.start, 0)
        self.assertEqual(len(resp.facets), 0)
        self.assertEqual(resp.facets, {})

    def test_response_from_search_request_with_facets(self):
        body = get_data('search_with_facets.json')
        resp = SolrResponse(body=body, status=200)
        self.assertTrue(resp.is_ok())
        self.assertEqual(len(resp.docs), 3)
        self.assertEqual(resp.num_found, 3)
        self.assertEqual(resp.start, 0)
        self.assertEqual(len(resp.facets), 2)
        self.assertEqual(resp.facets,
                         {u'portal_type': {u'Folder': 2, u'Document': 1},
                          u'review_state': {u'private': 3}})

    def test_response_from_search_with_highlighting(self):
        body = get_data('highlighting.json')
        resp = SolrResponse(body=body, status=200)
        self.assertTrue(resp.is_ok())
        self.assertIn('highlighting', resp)

    def test_response_from_schema_request(self):
        body = get_data('schema.json')
        resp = SolrResponse(body=body, status=200)
        self.assertTrue(resp.is_ok())
        self.assertIn('schema', resp)
