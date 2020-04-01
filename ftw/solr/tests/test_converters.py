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

    def test_datetime_before_1900_converts_to_iso8601(self):
        dt = to_iso8601(datetime(1871, 3, 30, 1, 2))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'1871-03-30T01:02:00.000Z')

    def test_datetime_before_1000_converts_to_iso8601(self):
        dt = to_iso8601(datetime(971, 3, 30, 17))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'0971-03-30T17:00:00.000Z')

    def test_datetime_before_100_converts_to_iso8601(self):
        dt = to_iso8601(datetime(71, 3, 30))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'0071-03-30T00:00:00.000Z')

    def test_python_date_converts_to_iso8601(self):
        dt = to_iso8601(date(2017, 10, 21))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'2017-10-21T00:00:00.000Z')

    def test_date_before_1900_converts_to_iso8601(self):
        dt = to_iso8601(date(1871, 3, 30))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'1871-03-30T00:00:00.000Z')

    def test_date_before_1000_converts_to_iso8601(self):
        dt = to_iso8601(date(971, 3, 30))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'0971-03-30T00:00:00.000Z')

    def test_date_before_100_converts_to_iso8601(self):
        dt = to_iso8601(date(71, 3, 30))
        self.assertIsInstance(dt, unicode)
        self.assertEqual(dt, u'0071-03-30T00:00:00.000Z')

    def test_invalid_date_converts_to_none(self):
        self.assertEqual(to_iso8601('30'), None)
        self.assertEqual(to_iso8601(30), None)

    def test_zope_datetime_high_millis_does_not_cause_rounding_error_low(self):
        dt = to_iso8601(DateTime('2017-10-21 16:28:59.999501'))
        self.assertIsInstance(dt, unicode)
        self.assertNotEqual(dt, u'2017-10-21T16:28:60.000Z')
        self.assertEqual(dt, u'2017-10-21T16:28:59.999Z')

    def test_zope_datetime_high_millis_does_not_cause_rounding_error_high(self):
        dt = to_iso8601(DateTime('2017-10-21 16:28:59.999999'))
        self.assertIsInstance(dt, unicode)
        self.assertNotEqual(dt, u'2017-10-21T16:28:60.000Z')
        self.assertEqual(dt, u'2017-10-21T16:28:59.999Z')

    def test_datetime_high_millis_does_not_cause_rounding_error_low(self):
        dt = to_iso8601(datetime(2017, 10, 21, 16, 28, 59, 999501))
        self.assertIsInstance(dt, unicode)
        self.assertNotEqual(dt, u'2017-10-21T16:28:60.000Z')
        self.assertEqual(dt, u'2017-10-21T16:28:59.999Z')

    def test_datetime_high_millis_does_not_cause_rounding_error_high(self):
        dt = to_iso8601(datetime(2017, 10, 21, 16, 28, 59, 999999))
        self.assertIsInstance(dt, unicode)
        self.assertNotEqual(dt, u'2017-10-21T16:28:60.000Z')
        self.assertEqual(dt, u'2017-10-21T16:28:59.999Z')

    def test_zope_and_python_datetimes_get_converted_identically_high_millis(self):
        tz = pytz.timezone('Europe/Zurich')
        python_datetime = tz.localize(datetime(2017, 10, 21, 16, 28, 59, 999999))
        zope_datetime = DateTime(python_datetime)
        self.assertEqual(to_iso8601(python_datetime), to_iso8601(zope_datetime))

    def test_zope_and_python_datetimes_get_converted_identically_low_millis(self):
        tz = pytz.timezone('Europe/Zurich')
        python_datetime = tz.localize(datetime(2017, 10, 21, 16, 28, 59, 111111))
        zope_datetime = DateTime(python_datetime)
        self.assertEqual(to_iso8601(python_datetime), to_iso8601(zope_datetime))


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
