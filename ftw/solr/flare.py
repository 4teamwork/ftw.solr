from collective.solr import flare
from collective.solr.interfaces import IFlare
from collective.solr.interfaces import ISolrFlare
from ftw.solr.interfaces import IFtwSolrLayer
from zope.component import adapts
from zope.interface import implements


# Customized PloneFlare which makes sure string values are returned as
# byte strings.
class PloneFlare(flare.PloneFlare):
    """A solr brain for search results"""
    implements(IFlare)
    adapts(ISolrFlare, IFtwSolrLayer)

    def __getattr__(self, name):
        """Look up attributes in dict"""
        value = super(PloneFlare, self).__getattr__(name)
        if isinstance(value, unicode):
            return value.encode('utf8')
        else:
            return value

    def getURL(self):
        if self.getRemoteUrl and self.getRemoteUrl.startswith('http'):
            return self.getRemoteUrl
        return super(PloneFlare, self).getURL()

