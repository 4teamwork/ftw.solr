# -*- coding: utf-8 -*-
from datetime import date
from DateTime import DateTime
from datetime import datetime
from ftw.solr.converters import to_iso8601
from ftw.solr.converters import to_unicode
import pytz
import unittest


class TestDateTimeConverter(unittest.TestCase):

    def test_zope_datetime_in_utc_converts_to_iso8601(self):
        dt = to_iso8601(DateTime('2017-10-21 14:28:16.936207 UTC'))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'2017-10-21T14:28:16.936Z')

    def test_zope_datetime_in_gmt2_converts_to_iso8601(self):
        dt = to_iso8601(DateTime('2017-10-21 16:28:16.936207 GMT+2'))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'2017-10-21T14:28:16.936Z')

    def test_python_datetime_timezone_naive_converts_to_iso8601(self):
        dt = to_iso8601(datetime(2017, 10, 21, 14, 28, 16, 936207))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'2017-10-21T14:28:16.936Z')

    def test_python_datetime_timezone_aware_converts_to_iso8601(self):
        tz = pytz.timezone('Europe/Zurich')
        dt = to_iso8601(tz.localize(
            datetime(2017, 10, 21, 16, 28, 16, 936207)))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'2017-10-21T14:28:16.936Z')

    def test_python_date_converts_to_iso8601(self):
        dt = to_iso8601(date(2017, 10, 21))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'2017-10-21T00:00:00.000Z')

    def test_invalid_date_converts_to_none(self):
        self.assertEqual(to_iso8601('30'), None)
        self.assertEqual(to_iso8601(30), None)


class TestStringConverter(unittest.TestCase):

    def test_bytestring_converts_to_unicode(self):
        string = to_unicode('fünf vor zwölf')
        self.assertIsInstance(string, unicode)
        self.assertEqual(string, u'fünf vor zwölf')

    def test_unicode_converts_to_unicode(self):
        string = to_unicode(u'fünf vor zwölf')
        self.assertIsInstance(string, unicode)
        self.assertEqual(string, u'fünf vor zwölf')

    def test_list_of_bytestrings_converts_to_list_of_unicode(self):
        strings = to_unicode(['fünf', 'vor', 'zwölf'], multivalued=True)
        for string in strings:
            self.assertIsInstance(string, unicode)
        self.assertEqual(strings, [u'fünf', u'vor', u'zwölf'])

    def test_tuple_of_bytestrings_converts_to_list_of_unicode(self):
        strings = to_unicode(('fünf', 'vor', 'zwölf'), multivalued=True)
        for string in strings:
            self.assertIsInstance(string, unicode)
        self.assertEqual(strings, [u'fünf', u'vor', u'zwölf'])

    def test_list_of_bytestrings_converts_to_unicode(self):
        string = to_unicode(['fünf', 'vor', 'zwölf'])
        self.assertIsInstance(string, unicode)
        self.assertEqual(string, u'fünf vor zwölf')

    def test_bytestring_converts_to_list_of_unicode(self):
        string = to_unicode('fünf vor zwölf', multivalued=True)
        self.assertIsInstance(string[0], unicode)
        self.assertEqual(string, [u'fünf vor zwölf'])
