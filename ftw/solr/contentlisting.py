from DateTime import DateTime
from ftw.solr.document import SolrDocument
from plone.app.contentlisting.contentlisting import BaseContentListingObject
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.app.layout.icons.interfaces import IContentIcon
from time import localtime
from zope.component import queryMultiAdapter
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import implementer


@implementer(IContentListing)
class SolrContentListing(object):

    doc_type = SolrDocument

    def __init__(self, resp):
        self.resp = resp

    def __getitem__(self, key):
        return self._create_content_listing_object(self.resp.docs[key])

    def __len__(self):
        return len(self.resp.docs)

    @property
    def actual_result_count(self):
        return self.resp.num_found

    def __iter__(self):
        for doc in self.resp.docs:
            yield self._create_content_listing_object(doc)

    def _create_content_listing_object(self, doc):
        doc = self.doc_type(doc)
        self._add_snippets(doc)
        return IContentListingObject(doc)

    def _add_snippets(self, doc):
        snippets = ''
        if 'highlighting' in self.resp:
            for snippet in self.resp['highlighting'].get(doc.UID).values():
                snippets += ' '.join(snippet)
        doc['_snippets_'] = snippets


@implementer(IContentListingObject)
class SolrContentListingObject(BaseContentListingObject):

    def __init__(self, doc):
        self.doc = doc

    @property
    def snippets(self):
        return self.doc.get('_snippets_')

    def Title(self):
        return self.doc.get('Title')

    def Description(self):
        return self.doc.get('Description')

    def Type(self):
        return self.doc.portal_type

    def created(self, zone=None):
        return self._zope_datetime('created', zone=zone)

    def modified(self, zone=None):
        return self._zope_datetime('modified', zone=zone)

    def effective(self, zone=None):
        return self._zope_datetime('effective', zone=zone)

    def expires(self, zone=None):
        return self._zope_datetime('expires', zone=zone)

    def CreationDate(self, zone=None):
        return self._dcmi_date('created', zone=zone)

    def ModificationDate(self, zone=None):
        return self._dcmi_date('modified', zone=zone)

    def EffectiveDate(self, zone=None):
        return self._dcmi_date('effective', zone=zone)

    def ExpirationDate(self, zone=None):
        return self._dcmi_date('expires', zone=zone)

    def _zope_datetime(self, field, zone=None):
        dt = self.doc.get(field)
        if dt is None:
            return None
        dt = DateTime(dt)
        if zone is None:
            zone = DateTime().localZone(localtime(dt.timeTime()))
        return dt.toZone(zone)

    def _dcmi_date(self, field, zone=None):
        dt = self._zope_datetime(field, zone=zone)
        if dt is not None:
            return dt.ISO8601()

    def getId(self):
        return self.doc.get('id')

    def getObject(self, REQUEST=None, restricted=True):
        return self.doc.getObject(REQUEST=REQUEST, restricted=restricted)

    def getDataOrigin(self):
        return self.doc

    def getPath(self):
        return self.doc.get('path')

    def getURL(self, relative=False):
        return self.doc.getURL(relative=relative)

    def uuid(self):
        return self.doc.get('UID')

    def getIcon(self):
        return queryMultiAdapter((getSite(), getRequest(), self.doc),
                                 interface=IContentIcon)()

    def getSize(self):
        return self.doc.get('getObjSize')

    def review_state(self):
        return self.doc.get('review_state')

    def PortalType(self):
        return self.doc.get('portal_type')

    def CroppedDescription(self):
        return self.doc.get('Description')
