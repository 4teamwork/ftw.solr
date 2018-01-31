from zope.component.hooks import getSite
from zope.globalrequest import getRequest


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

    @property
    def getId(self):
        return self.data.get('id')

    def getPath(self):
        return self.path

    def getURL(self, relative=False):
        request = getRequest()
        return request.physicalPathToURL(self.getPath(), relative)

    def getObject(self, REQUEST=None, restricted=True):
        site = getSite()
        path = self.getPath()
        if not path:
            return None
        path = path.split('/')
        if restricted:
            parent = site.unrestrictedTraverse(path[:-1], None)
            if parent is None:
                return None
            return parent.restrictedTraverse(path[-1], None)
        return site.unrestrictedTraverse(path, None)


def unicode2bytes(data):
    if isinstance(data, unicode):
        return data.encode('utf8')
    elif isinstance(data, dict):
        return dict(map(unicode2bytes, data.iteritems()))
    elif isinstance(data, (list, tuple)):
        return list(map(unicode2bytes, data))
    else:
        return data
