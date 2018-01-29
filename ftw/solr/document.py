class SolrDocument(object):

    def __init__(self, data, fields=None):
        self.data = unicode2bytes(data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getattr__(self, name):
        if name in self.data:
            val = self.data[name]
            if isinstance(val, unicode):
                val = val.encode('utf8')
            return val
        else:
            raise AttributeError

    def Title(self):
        return self.data.get('Title')

    @property
    def getId(self):
        return self.data.get('id')


def unicode2bytes(data):
    if isinstance(data, unicode):
        return data.encode('utf8')
    elif isinstance(data, dict):
        return dict(map(unicode2bytes, data.iteritems()))
    elif isinstance(data, (list, tuple)):
        return list(map(unicode2bytes, data))
    else:
        return data
