from DateTime import DateTime
from OFS.Traversable import path2url
from plone.app.contentlisting.contentlisting import BaseContentListingObject
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.contentlisting.interfaces import IContentListingObject
from zope.component.hooks import getSite
from zope.interface import implementer


@implementer(IContentListing)
class SolrContentListing(object):

    def __init__(self, resp):
        self.resp = resp

    def __getitem__(self, key):
        return SolrContentListingObject(self.resp.docs[key])

    def __len__(self):
        return len(self.resp.docs)

    @property
    def actual_result_count(self):
        return self.resp.num_found

    def __iter__(self):
        for doc in self.resp.docs:
            yield SolrContentListingObject(doc)

    def add_snippets(self, doc):
        uid = doc['UID']
        snippets = ''
        if 'highlighting' in self.resp:
            for snippet in self.resp['highlighting'].get(uid).values():
                snippets += ' '.join(snippet)
        doc['_snippets_'] = snippets


@implementer(IContentListingObject)
class SolrContentListingObject(BaseContentListingObject):

    def __init__(self, doc):
        self.doc = doc

    def __getattr__(self, name):
        if name in self.doc:
            val = self.doc[name]
            if isinstance(val, unicode):
                val = val.encode('utf8')
            return val
        elif name.startswith(u'_'):
            raise AttributeError
        else:
            return None
            raise AttributeError

    @property
    def snippets(self):
        return self.doc.get('_snippets_')

    def getId(self):
        return self.doc.id

    def getObject(self, REQUEST=None, restricted=True):
        site = getSite()
        path = self.getPath()
        if not path:
            return None
        path = path.split('/')
        if restricted:
            parent = site.unrestrictedTraverse(path[:-1])
            return parent.restrictedTraverse(path[-1])
        return site.unrestrictedTraverse(path)

    def getDataOrigin(self):
        return self.doc

    def getPath(self):
        return self.path

    def getURL(self, relative=False):
        path = self.getPath()
        path = path.encode('utf-8')
        try:
            url = self.request.physicalPathToURL(path, relative)
        except AttributeError:
            url = path2url(path.split('/'))
        return url

    def uuid(self):
        return self.doc.UID

    def getIcon(self):
        return self.doc.getIcon

    def getSize(self):
        return self.doc.getSize

    def review_state(self):
        return self.doc.review_state

    def PortalType(self):
        return self.doc.portal_type

    def CroppedDescription(self):
        return self.doc.Description

    def CreationDate(self, zone=None):
        created = self.doc.get('created')
        if created is None:
            return None
        return DateTime(created)

    def ModificationDate(self, zone=None):
        modified = self.doc.get('modified')
        if modified is None:
            return None
        return DateTime(modified)
