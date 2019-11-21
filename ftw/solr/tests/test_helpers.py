# -*- coding: utf-8 -*-
from ftw.solr.helpers import chunked_file_reader
from ftw.solr.helpers import http_chunked_encoder
from StringIO import StringIO
import unittest


class TestHelpers(unittest.TestCase):

    def test_chunked_file_reader(self):
        fileobj = StringIO("Lorem Ipsum")
        reader = chunked_file_reader(fileobj, chunk_size=3)
        self.assertEqual(['Lor', 'em ', 'Ips', 'um'], list(reader))

    def test_http_chunked_encoder(self):
        encoder = http_chunked_encoder(['Lorem', 'Ipsum.'])
        self.assertEqual(
            ['5\r\nLorem\r\n', '6\r\nIpsum.\r\n', '0\r\n\r\n'],
            list(encoder))
