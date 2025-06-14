from ftw.solr.connection import local_data
from ftw.solr.connection import SolrConnection
from ftw.solr.connection import SolrConnectionConfig
from ftw.solr.connection import SolrConnectionManager
from ftw.solr.connection import SolrResponse
from ftw.solr.interfaces import ISolrConnectionConfig
from ftw.solr.interfaces import ISolrSettings
from ftw.solr.testing import FTW_SOLR_INTEGRATION_TESTING
from ftw.solr.tests.utils import get_data
from ftw.solr.tests.utils import MockBlob
from ftw.solr.tests.utils import MockHTTPResponse
from mock import MagicMock
from mock import patch
from plone.registry.interfaces import IRegistry
from plone.testing import zca
from zope.component import provideUtility
from zope.component import queryUtility

import json
import os
import socket
import transaction
import unittest


class TestConnection(unittest.TestCase):

    layer = FTW_SOLR_INTEGRATION_TESTING

    def assert_equal_commands(self, first, second):
        return self.assertEqual(
            json.loads('{' + ','.join(first) + '}'),
            json.loads('{' + ','.join(second) + '}'))

    def test_connection_initialization(self):
        conn = SolrConnection(host='mysolrserver', base='/solr/mycore')
        self.assertEqual(conn.conn.host, 'mysolrserver')
        self.assertEqual(conn.conn.port, 8983)
        self.assertEqual(conn.base, '/solr/mycore')

    @patch('ftw.solr.connection.HTTPConnection', autospec=True)
    def test_successful_request_returns_response(self, MockHTTPConnection):
        MockHTTPConnection.return_value.request.return_value = None
        MockHTTPConnection.return_value.getresponse.return_value = (
            MockHTTPResponse(body=get_data('search.json')))
        conn = SolrConnection(base='/solr/mycore')
        resp = conn.request('POST', '/select', data='{"query":"*:*" }')
        self.assertEqual(resp.http_status, 200)

    @patch('ftw.solr.connection.HTTPConnection', autospec=True)
    def test_broken_connection_returns_response(self, MockHTTPConnection):
        exception = socket.error(61, 'Connection refused')
        MockHTTPConnection.return_value.request.side_effect = exception
        conn = SolrConnection(base='/solr/mycore')
        resp = conn.request('POST', '/select', data='{"query":"*:*" }')
        self.assertEqual(resp.exception, exception)

    @patch('ftw.solr.connection.HTTPConnection', autospec=True)
    def test_broken_connection_returns_response_after_reconnect(
            self, MockHTTPConnection):
        exception = socket.error(61, 'Connection refused')
        MockHTTPConnection.return_value.request.side_effect = [exception, None]
        MockHTTPConnection.return_value.getresponse.return_value = (
            MockHTTPResponse(body=get_data('search.json')))
        conn = SolrConnection(base='/solr/mycore')
        resp = conn.request('POST', '/select', data='{"query":"*:*" }')
        self.assertEqual(resp.http_status, 200)
        self.assertEqual(resp.exception, None)

    def test_add_operation_queues_update_command(self):
        conn = SolrConnection()
        conn.add({'id': '1'})
        self.assertEqual(conn.update_commands, ['"add": {"doc": {"id": "1"}}'])

    def test_extract_operation_queues_extract_command(self):
        conn = SolrConnection()
        conn.extract('Blob', 'SearchableText', {'id': '1'},
                     'application/octet-stream')
        self.assertEqual(
            conn.extract_commands,
            [('Blob', 'SearchableText', {'id': '1'}, 'application/octet-stream')])

    def test_delete_operation_queues_update_command(self):
        conn = SolrConnection()
        conn.delete('1')
        self.assertEqual(conn.update_commands, ['"delete": {"id": "1"}'])

    def test_delete_by_query_operation_queues_update_command(self):
        conn = SolrConnection()
        conn.delete_by_query('*:*')
        self.assertEqual(conn.update_commands, ['"delete": {"query": "*:*"}'])

    def test_commit_operation_queues_update_command_and_flushes_queue(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.flush = MagicMock(name='flush')
        conn.commit()
        conn.flush.assert_called_once_with(after_commit=True)
        self.assert_equal_commands(
            conn.update_commands,
            ['"commit": {"softCommit": true, "waitSearcher": true}'])

    def test_optimize_operation_queues_update_command_and_flushes_queue(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.flush = MagicMock(name='flush')
        conn.optimize()
        conn.flush.assert_called_once()
        self.assertEqual(
            conn.update_commands, ['"optimize": {"waitSearcher": true}'])

    def test_flush_operation_posts_update_commands_and_clears_queue_if_post_commit_hook_disabled(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(ISolrSettings)
        settings.enable_updates_in_post_commit_hook = False

        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post', return_value=SolrResponse(
            body='{"responseHeader":{"status":0}}', status=200))
        conn.add({'id': '1'})
        conn.flush()
        conn.post.assert_called_once_with(
            '/update', data='{"add": {"doc": {"id": "1"}}}', log_error=False)
        self.assertEqual(conn.update_commands, [])

    def test_flush_operation_adds_updates_to_post_commit_hook_if_enabled(self):
        hooks = list(transaction.get().getAfterCommitHooks())
        self.assertEqual(0, len(hooks))

        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post', return_value=SolrResponse(
            body='{"responseHeader":{"status":0}}', status=200))
        conn.add({'id': '1'})
        conn.flush()
        self.assertEqual(conn.update_commands, [])
        self.assertEqual(0, conn.post.call_count)

        hooks = list(transaction.get().getAfterCommitHooks())
        self.assertEqual(1, len(hooks))
        hook = hooks[0]
        hook[0](True, *hook[1], **hook[2])

        self.assertEqual(1, conn.post.call_count)
        conn.post.assert_called_once_with(
            '/update', data='{"add": {"doc": {"id": "1"}}}', log_error=False)

    def test_flush_operation_posts_extract_commands_and_clears_queue(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post')
        conn.post.return_value.body.get.return_value = 'The searchable text'
        tr = transaction.begin()
        conn.extract(MockBlob(), 'SearchableText', {'id': '1'},
                     'application/octet-stream')
        conn.flush()
        tr.commit()
        args, kwargs = conn.post.call_args_list[0]
        self.assertEqual(
            args,
            ('/update/extract?extractOnly=true&stream.file=%2Ffolder%2Ffile',))
        self.assertEqual(
            kwargs,
            {'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
             'log_error': False},
        )
        args, kwargs = conn.post.call_args_list[1]
        self.assertEqual(args, ('/update',))
        self.assertEqual(
            kwargs,
            {'data': '{"add": {"doc": {"SearchableText": {"set": "The '
                     'searchable text"}, "id": "1"}}}',
             'log_error': False})
        self.assertEqual(conn.extract_commands, [])

    def test_flush_operation_posts_filtered_extract_commands(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post')
        conn.post.return_value.body.get.return_value = 'The searchable text'
        tr = transaction.begin()
        conn.extract(MockBlob('file1'), 'SearchableText', {'UID': '1'},
                     'application/octet-stream')
        conn.extract(MockBlob('file2'), 'SearchableText', {'UID': '2'},
                     'application/octet-stream')
        conn.extract(MockBlob('file3'), 'SearchableText', {'UID': '2'},
                     'application/octet-stream')
        conn.extract(MockBlob('file4'), 'OtherField', {'UID': '1'},
                     'application/octet-stream')
        conn.flush()
        tr.commit()

        self.assertEqual(6, len(conn.post.call_args_list))

        self.assertEqual(
            (('/update/extract?extractOnly=true&stream.file=file1',),
             {'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
              'log_error': False}),
            conn.post.call_args_list[0])

        self.assertEqual(
            (('/update',),
             {'data': '{"add": {"doc": {"SearchableText": {"set": '
                      '"The searchable text"}, "UID": "1"}}}',
              'log_error': False}),
            conn.post.call_args_list[1])

        self.assertEqual(
            (('/update/extract?extractOnly=true&stream.file=file3',),
             {'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
              'log_error': False}),
            conn.post.call_args_list[2])

        self.assertEqual(
            (('/update',),
             {'data': '{"add": {"doc": {"SearchableText": {"set": '
                      '"The searchable text"}, "UID": "2"}}}',
              'log_error': False}),
            conn.post.call_args_list[3])

        self.assertEqual(
            (('/update/extract?extractOnly=true&stream.file=file4',),
             {'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
              'log_error': False}),
            conn.post.call_args_list[4])

        self.assertEqual(
            (('/update',),
             {'data': '{"add": {"doc": {"OtherField": {"set": '
                      '"The searchable text"}, "UID": "1"}}}',
              'log_error': False}),
            conn.post.call_args_list[5])
        self.assertEqual(conn.extract_commands, [])

    def test_flush_operation_posts_extract_commands_with_blobs_if_configured(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.upload_blobs = True
        conn.post = MagicMock(name='post')
        conn.post_chunked = MagicMock(name='post_chunked')
        conn.post_chunked.return_value.body.get.return_value = 'The searchable text'
        tr = transaction.begin()
        blob = MockBlob()
        conn.extract(blob, 'SearchableText', {'id': '1'},
                     'application/octet-stream')
        conn.flush()
        tr.commit()
        args, kwargs = conn.post_chunked.call_args_list[0]
        self.assertEqual(
            args,
            ('/update/extract?extractOnly=true', blob))
        self.assertEqual(
            kwargs,
            {'content_type': 'application/octet-stream',
             'log_error': False},
        )
        args, kwargs = conn.post.call_args_list[0]
        self.assertEqual(args, ('/update',))
        self.assertEqual(
            kwargs,
            {'data': '{"add": {"doc": {"SearchableText": {"set": "The '
                     'searchable text"}, "id": "1"}}}',
             'log_error': False})

        self.assertEqual(conn.extract_commands, [])

    def test_flush_operation_without_after_commit_hook(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post')
        conn.post.return_value.body.get.return_value = 'The searchable text'
        conn.extract(MockBlob(), 'SearchableText', {'id': '1'},
                     'application/octet-stream')
        conn.flush(after_commit=False)

        args, kwargs = conn.post.call_args_list[0]
        self.assertEqual(
            args,
            ('/update/extract?extractOnly=true&stream.file=%2Ffolder%2Ffile',))
        self.assertEqual(
            kwargs,
            {'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
             'log_error': False},
        )
        args, kwargs = conn.post.call_args_list[1]
        self.assertEqual(args, ('/update',))
        self.assertEqual(
            kwargs,
            {'data': '{"add": {"doc": {"SearchableText": {"set": "The '
                     'searchable text"}, "id": "1"}}}',
             'log_error': False})

        self.assertEqual(conn.extract_commands, [])

    @patch('ftw.solr.connection.HTTPConnection', autospec=True)
    def test_extract_with_tika(self, MockHTTPConnection):
        tika_conn = MockHTTPConnection.return_value
        tika_conn.getresponse.return_value = MockHTTPResponse(body='extracted by tika')
        os.environ['SOLR_TIKA_URL'] = 'http://tikaserver:9998/tika'
        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post')

        tr = transaction.begin()
        blob = MockBlob(
            path=os.path.join(os.path.dirname(__file__), 'data', 'file.blob'))
        conn.extract(blob, 'SearchableText', {'UID': '1'},
                     'application/octet-stream')
        conn.flush()
        tr.commit()

        tika_conn.putrequest.assert_called_with('PUT', '/tika')
        conn.post.assert_called_once_with(
            '/update',
            data='{"add": {"doc": {"SearchableText": {"set": "extracted by tika"}, "UID": "1"}}}',  # noqa
            log_error=False,
        )

        self.assertEqual(conn.extract_commands, [])
        del os.environ['SOLR_TIKA_URL']

    @patch('ftw.solr.connection.HTTPConnection', autospec=True)
    def test_extract_with_invalid_tika_response(self, MockHTTPConnection):
        tika_conn = MockHTTPConnection.return_value
        tika_conn.getresponse.return_value = MockHTTPResponse(status=404, body='Not Found')
        os.environ['SOLR_TIKA_URL'] = 'http://tikaserver:9998/tika'
        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post')

        tr = transaction.begin()
        blob = MockBlob(
            path=os.path.join(os.path.dirname(__file__), 'data', 'file.blob'))
        conn.extract(blob, 'SearchableText', {'UID': '1'},
                     'application/octet-stream')
        conn.flush()
        tr.commit()

        tika_conn.putrequest.assert_called_with('PUT', '/tika')
        conn.post.assert_called_once_with(
            '/update',
            data='{"add": {"doc": {"SearchableText": {"set": null}, "UID": "1"}}}',  # noqa
            log_error=False,
        )

        self.assertEqual(conn.extract_commands, [])
        del os.environ['SOLR_TIKA_URL']

    @patch('ftw.solr.connection.HTTPConnection', autospec=True)
    def test_extract_with_tika_exception(self, MockHTTPConnection):
        tika_conn = MockHTTPConnection.return_value
        exception = socket.error(61, 'Connection refused')
        tika_conn.putrequest.side_effect = exception
        os.environ['SOLR_TIKA_URL'] = 'http://tikaserver:9998/tika'
        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post')

        tr = transaction.begin()
        blob = MockBlob(
            path=os.path.join(os.path.dirname(__file__), 'data', 'file.blob'))
        conn.extract(blob, 'SearchableText', {'UID': '1'},
                     'application/octet-stream')
        conn.flush()
        tr.commit()

        tika_conn.putrequest.assert_called_with('PUT', '/tika')
        conn.post.assert_called_once_with(
            '/update',
            data='{"add": {"doc": {"SearchableText": {"set": null}, "UID": "1"}}}',  # noqa
            log_error=False,
        )

        self.assertEqual(conn.extract_commands, [])
        del os.environ['SOLR_TIKA_URL']

    def test_abort_operation_clears_queue(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.add({'id': '1'})
        conn.extract(MockBlob(), 'SearchableText', {'id': '1'},
                     'application/octet-stream')
        conn.abort()
        self.assertEqual(conn.update_commands, [])
        self.assertEqual(conn.extract_commands, [])

    def test_search_operation_posts_search_request(self):
        conn = SolrConnection(base='/solr/mycore')
        conn.post = MagicMock(name='post')
        conn.search({'query': '*:*'})
        conn.post.assert_called_once_with('/select', '{"query": "*:*"}')


class TestConnectionManager(unittest.TestCase):

    layer = zca.UNIT_TESTING

    def setUp(self):
        if hasattr(local_data, 'connection'):
            del local_data.connection

    def test_manager_creates_new_connection(self):
        manager = SolrConnectionManager()
        config = SolrConnectionConfig('myhost', 8983, '/solr/mycore')
        provideUtility(config, ISolrConnectionConfig)
        conn = manager.connection
        self.assertEqual(conn.host, 'myhost')
        self.assertEqual(conn.port, 8983)
        self.assertEqual(conn.base, '/solr/mycore')

    def test_manager_reuses_existing_connection(self):
        manager = SolrConnectionManager()
        config = SolrConnectionConfig('myhost', 8983, '/solr/mycore')
        provideUtility(config, ISolrConnectionConfig)
        conn1 = manager.connection
        conn2 = manager.connection
        self.assertEqual(conn1, conn2)

    def test_manager_returns_none_with_no_config(self):
        manager = SolrConnectionManager()
        conn = manager.connection
        self.assertEqual(conn, None)

    def test_manager_creates_new_schema(self):
        manager = SolrConnectionManager()
        config = SolrConnectionConfig('myhost', 8983, '/solr/mycore')
        provideUtility(config, ISolrConnectionConfig)
        schema = manager.schema
        self.assertIn('unique_key', dir(schema))
        self.assertIn('fields', dir(schema))

    def test_manager_reuses_existing_schema(self):
        manager = SolrConnectionManager()
        config = SolrConnectionConfig('myhost', 8983, '/solr/mycore')
        provideUtility(config, ISolrConnectionConfig)
        schema1 = manager.schema
        schema1.unique_key = u'UID'  # Make it a 'valid' schema
        schema2 = manager.schema
        self.assertEqual(schema1, schema2)
