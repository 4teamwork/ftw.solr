from DateTime import DateTime
from datetime import datetime
from datetime import date
import math


def to_iso8601(value, multivalued=False):
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        millisecond, second = math.modf(v.second())
        value = u'%04d-%02d-%02dT%02d:%02d:%02d.%03dZ' % (
            v.year(), v.month(), v.day(), v.hour(), v.minute(),
            int(second), millisecond * 1000
        )
    elif isinstance(value, datetime):
        if value.tzinfo is not None:
            # Convert to timezone naive in UTC
            value = (value - value.utcoffset()).replace(tzinfo=None)

        value = u'%04d-%02d-%02dT%02d:%02d:%02d.%03dZ' % (
            value.year, value.month, value.day, value.hour, value.minute,
            value.second, value.microsecond / 1000
        )
    elif isinstance(value, date):
        value = u'%04d-%02d-%02dT%02d:%02d:%02d.%03dZ' % (
            value.year, value.month, value.day, 0, 0, 0, 0
        )
    else:
        value = None
    return value


def to_unicode(value, multivalued=False):
    if isinstance(value, tuple):
        value = list(value)
    if not isinstance(value, list):
        value = [value]
    for i, v in enumerate(value):
        if isinstance(v, str):
            v = v.decode('utf8')
        value[i] = v
    if not multivalued:
        if len(value) > 1:
            return u' '.join(value)
        else:
            return value[0]
    return value


CONVERTERS = {
    'solr.DatePointField': to_iso8601,
    'solr.StrField': to_unicode,
}
