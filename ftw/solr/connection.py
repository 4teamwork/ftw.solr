from ftw.solr.interfaces import ISolrConnectionConfig
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.schema import SolrSchema
from httplib import HTTPConnection
from httplib import HTTPException
from logging import getLogger
from threading import local
from urllib import urlencode
from zope.component import queryUtility
from zope.interface import implementer
import json
import socket
import transaction


logger = getLogger('ftw.solr.connection')

# a thread-local object holding the connection
local_data = local()


@implementer(ISolrConnectionConfig)
class SolrConnectionConfig(object):

    def __init__(self, host, port, base):
        self.host = host
        self.port = port
        self.base = base


class SolrConnection(object):

    post_headers = {'Content-Type': 'application/json'}

    def __init__(self, host='localhost', port=8983, base='/solr',
                 timeout=None):
        self.timeout = timeout
        self.host = host
        self.port = port
        self.base = base
        self.conn = HTTPConnection(self.host, self.port, timeout=self.timeout)
        self.update_commands = []
        self.extract_commands = []
        self.reconnect_before_request = False

    def request(self, method, path, data=None, headers={}, log_error=True):
        try:
            if self.reconnect_before_request:
                self.reconnect()
            self.conn.request(
                method, self.base + path, body=data, headers=headers)
            resp = self.conn.getresponse()
            body = resp.read()
            status = resp.status
            self.reconnect_before_request = False
            return SolrResponse(body, status, log_error=log_error)
        except (socket.error, HTTPException) as exc:
            if not self.reconnect_before_request:
                self.reconnect_before_request = True
                return self.request(method, path, data=data, headers=headers)
            else:
                self.reconnect_before_request = False
                return SolrResponse(exception=exc, log_error=log_error)

    def post(self, path, data=None, headers={}, log_error=True):
        headers = headers if headers else self.post_headers
        return self.request(
            'POST', path, data, headers, log_error=log_error)

    def get(self, path, headers={}, log_error=True):
        return self.request('GET', path, headers=headers, log_error=log_error)

    def reconnect(self):
        self.conn.close()
        self.conn.connect()

    def add(self, data):
        self.update_commands.append('"add": ' + json.dumps({'doc': data}))

    def extract(self, blob, data):
        """Add blob using Solr's Extracting Request Handler."""
        self.extract_commands.append((blob, data))

    def delete(self, id_):
        self.update_commands.append(
            '"delete": ' + json.dumps({'id': id_}))

    def delete_by_query(self, query):
        self.update_commands.append(
            '"delete": ' + json.dumps({'query': query}))

    def commit(self, wait_searcher=False, extract_after_commit=True):
        self.update_commands.append(
            '"commit": ' + json.dumps({'waitSearcher': wait_searcher}))
        self.flush(extract_after_commit=extract_after_commit)

    def optimize(self, wait_searcher=False):
        self.update_commands.append(
            '"optimize": ' + json.dumps({'waitSearcher': wait_searcher}))

    def flush(self, extract_after_commit=True):
        """Send queued update commands to Solr."""
        if self.update_commands:
            data = '{%s}' % ','.join(self.update_commands)
            resp = self.post('/update', data=data, log_error=False)
            if not resp.is_ok():
                logger.error('Update command failed. %s', resp.error_msg())
            self.update_commands = []

        if self.extract_commands:
            def hook(succeeded, extract_commands):
                if not succeeded:
                    return
                for blob, data in extract_commands:
                    file_ = blob.committed()
                    params = {}
                    for k, v in data.items():
                        k = k.encode('utf8')
                        if isinstance(v, unicode):
                            v = v.encode('utf8')
                        elif isinstance(v, list):
                            v = [vv.encode('utf8') for vv in v]
                        elif isinstance(v, bool):
                            v = 'true' if v else 'false'
                        params['literal.%s' % k] = v
                    params['stream.file'] = file_
                    params['commitWithin'] = '10000'
                    resp = self.post(
                        '/update/extract?%s' % urlencode(params, doseq=True),
                        headers={'Content-Type': 'application/x-www-form-urlencoded'},  # noqa
                        log_error=False)
                    if not resp.is_ok():
                        logger.error(
                            'Extract command for UID=%s with blob %s failed. '
                            '%s',
                            data.get(u'UID'), file_, resp.error_msg())
            if extract_after_commit:
                transaction.get().addAfterCommitHook(
                    hook, args=[self.extract_commands])
            else:
                hook(True, self.extract_commands)
            self.extract_commands = []

    def abort(self):
        """Abort all pending commands."""
        # While Solr supports rollback we can't use it because there could be
        # other uncommitted operations from other connections and those would
        # be rollbacked too. Thus we delay sending anything to Solr until the
        # next commit.
        self.update_commands = []
        self.extract_commands = []

    def search(self, params, request_handler='/select'):
        return self.post(request_handler, json.dumps(params))

    def __repr__(self):
        return "SolrConnection(host='%s', port=%s, base='%s') at 0x%x" % (
            self.host, self.port, self.base, id(self))


_no_connection_marker = object()


@implementer(ISolrConnectionManager)
class SolrConnectionManager(object):

    @property
    def connection(self):
        conn = getattr(local_data, 'connection', _no_connection_marker)
        if conn is _no_connection_marker:
            config = queryUtility(ISolrConnectionConfig)
            if config is not None:
                conn = SolrConnection(
                    host=config.host, port=config.port, base=config.base)
            else:
                conn = None
                logger.warning('Solr configuration missing.')
            setattr(local_data, 'connection', conn)
        return conn

    @property
    def schema(self):
        schema = getattr(local_data, 'schema', None)
        if not schema:
            schema = SolrSchema(manager=self)
            setattr(local_data, 'schema', schema)
        return schema


class SolrResponse(object):

    def __init__(self, body='null', status=None, exception=None,
                 log_error=True):
        self.http_status = status
        self.exception = exception
        self.status = -1
        self.qtime = 0
        self.params = None
        self.docs = []
        self.num_found = 0
        self.start = 0
        self.body = {}
        if self.http_status:
            self.parse(body)
        if log_error and not self.is_ok():
            logger.error('Solr response error. %s', self.error_msg())

    def parse(self, data):
        try:
            data = json.loads(data)
        except ValueError:
            data = None
        if data is None:
            return

        response_header = data.get(u'responseHeader', {})
        self.status = response_header.get(u'status', self.status)
        self.qtime = response_header.get(u'QTime', 0)
        self.params = json.loads(response_header.get(u'params', {}).get(
            u'json', 'null'))

        if u'response' in data:
            self.docs = data[u'response'].get(u'docs', [])
            self.num_found = data[u'response'].get(u'numFound', 0)
            self.start = data[u'response'].get(u'start', 0)

        self.body = data

    def is_ok(self):
        if self.http_status == 200 and self.status == 0:
            return True
        return False

    def error_msg(self):
        if self.exception is not None:
            return 'An exception occured: %s' % str(self.exception)
        elif self.http_status:
            if u'error' in self.body and u'msg' in self.body[u'error']:
                return 'Server responded with code %s, %s.' % (
                    self.http_status,
                    self.body[u'error'][u'msg'].encode('utf8'))
            else:
                return 'Server responded with code %s.' % self.http_status
        else:
            return 'An unknown error occured.'

    def get(self, key, default=None):
        return self.body.get(key, default)

    def __getitem__(self, key):
        return self.body[key]

    def __contains__(self, key):
        return key in self.body

    def __repr__(self):
        if self.is_ok():
            return 'SolrResponse(%s docs)' % len(self.docs)
        elif self.exception is not None:
            return 'SolrResponse(exception=%r)' % self.exception
        return "SolrResponse(status=%s)" % self.http_status
