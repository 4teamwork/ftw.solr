from plone.app.contentlisting import catalog
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.app.layout.icons.interfaces import IContentIcon
from zope.interface import implements
from zope.component import queryMultiAdapter
from zope.component.hooks import getSite
from DateTime import DateTime

timezone = DateTime().timezone()


class SolrContentListingObject(catalog.CatalogContentListingObject):
    
    implements(IContentListingObject)

    def __init__(self, flare):
        self._brain = flare
        self._cached_realobject = None
        self.request = flare.request
        self.context = getSite()

    def __repr__(self):
        return "<ftw.solr.contentlisting." + \
               "SolrContentListingObject instance at %s>" % (
            self.getPath(), )

    def EffectiveDate(self, zone=timezone):
        return self._brain.effective.toZone(zone).ISO8601()

    def ExpirationDate(self, zone=timezone):
        return self._brain.expires.toZone(zone).ISO8601()

    def getIcon(self):
        return queryMultiAdapter((self.context, self.request,
                                  self._brain), interface=IContentIcon)()
