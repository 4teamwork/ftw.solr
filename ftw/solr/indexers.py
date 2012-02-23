from zope.component import getMultiAdapter
from zope.interface import Interface
from plone.indexer import indexer


@indexer(Interface)
def site_section(obj, **kwargs):
    """An indexer which returns the section title for a content item.
    """
    portal_state = getMultiAdapter((obj, obj.REQUEST),
                                   name=u'plone_portal_state')
    navroot = portal_state.navigation_root()
    contentPath = obj.getPhysicalPath()[len(navroot.getPhysicalPath()):]
    if contentPath:
        section = navroot.unrestrictedTraverse(contentPath[0])
        return section.Title()
    return ''
