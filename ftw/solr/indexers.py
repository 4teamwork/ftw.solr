import re
from zope.component import getMultiAdapter
from zope.interface import Interface
from plone.indexer import indexer
from Products.CMFCore.utils import getToolByName


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


@indexer(Interface)
def creator_fullname(obj, **kwargs):
    """An indexer which returns the full name of the content creator.
    """
    creator = obj.Creator()
    mtool = getToolByName(obj, 'portal_membership')
    member_info = mtool.getMemberInfo(creator)
    if member_info and member_info['fullname']:
        return member_info['fullname']
    return creator


@indexer(Interface)
def snippet_text(obj, **kwargs):
    """Text for snippets (aka highlighting) in search results.
       Uses the SearchableText but excludes some fields that should not be
       shown in search results.
    """
    text = obj.SearchableText()
    for fieldname in ['id', 'title', 'searchwords']:
        field = obj.Schema().getField(fieldname)
        if field is None:
            continue

        method = field.getIndexAccessor(obj)
        value = method()
        text = text.replace(value, '', 1)

    # Strip html tags
    text = re.sub('<[^<]+?>', '', text)

    return text
