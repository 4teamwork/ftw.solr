from DateTime import DateTime
from datetime import datetime
from datetime import date


def to_iso8601(value, multivalued=False):
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = u'%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (
            v.year(), v.month(), v.day(), v.hour(), v.minute(), v.second()
        )
    elif isinstance(value, datetime):
        if value.tzinfo is not None:
            # Convert to timezone naive in UTC
            value = (value - value.utcoffset()).replace(tzinfo=None)
        value = u'%s.%03dZ' % (
            value.strftime('%Y-%m-%dT%H:%M:%S'),
            value.microsecond / 1000
        )
    elif isinstance(value, date):
        value = value.strftime('%Y-%m-%dT%H:%M:%S.000Z').decode()
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
