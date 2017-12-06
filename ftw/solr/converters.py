from DateTime import DateTime
from datetime import datetime


def datetime_converter(value, multivalued):
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = '%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (
            v.year(), v.month(), v.day(), v.hour(), v.minute(), v.second()
        )
    elif isinstance(value, datetime):
        # Convert a timezone aware timetuple to a non timezone aware time
        # tuple representing utc time. Does nothing if object is not
        # timezone aware
        value = datetime(*value.utctimetuple()[:7])
        value = '%s.%03dZ' % (
            value.strftime('%Y-%m-%dT%H:%M:%S'),
            value.microsecond % 1000
        )
    return value


def str_converter(value, multivalued):
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
            return u', '.join(value)
        else:
            return value[0]
    return value


CONVERTERS = {
    'solr.DatePointField': datetime_converter,
    'solr.StrField': str_converter,
}
