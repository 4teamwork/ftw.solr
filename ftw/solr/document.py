from ftw.solr.interfaces import ISolrDocument
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import implementer


@implementer(ISolrDocument)
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
            return self.data[name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name))

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
        segments = path.split('/')
        if restricted:
            parent = site.unrestrictedTraverse(segments[:-1], None)
            if parent is None:
                return None
            obj = parent.restrictedTraverse(segments[-1], None)
        else:
            obj = site.unrestrictedTraverse(segments, None)
        # If there's no object at the given path we can still get one through
        # acquisition, but that's not what we want.
        if obj is not None and '/'.join(obj.getPhysicalPath()) == path:
            return obj
        else:
            return None


def unicode2bytes(data):
    if isinstance(data, unicode):
        return data.encode('utf8')
    elif isinstance(data, dict):
        return dict(map(unicode2bytes, data.iteritems()))
    elif isinstance(data, (list, tuple)):
        return list(map(unicode2bytes, data))
    else:
        return data
