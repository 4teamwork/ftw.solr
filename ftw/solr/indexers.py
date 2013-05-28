import re
from plone.indexer import indexer
from plone.indexer.interfaces import IIndexer
from plone.indexer.wrapper import IndexableObjectWrapper
from Products.Archetypes.interfaces.base import IBaseObject
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.utils import getToolByName
from Products.PluginIndexes.common import safe_callable
from Products.ZCatalog.interfaces import IZCatalog
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.interface import implements
from zope.interface import Interface


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


class SnippetTextIndexer(object):
    """Text for snippets (aka highlighting) in search results.
       Uses the SearchableText but excludes some fields that should not be
       shown in search results.
    """
    implements(IIndexer)
    adapts(Interface, IZCatalog)

    def __init__(self, context, catalog):
        self.context = context
        self.catalog = catalog

    def __call__(self):
        wrapped = IndexableObjectWrapper(self.context, self.catalog)
        text = getattr(wrapped, 'SearchableText')
        if safe_callable(text):
            text = text()

        # Archetypes object: remove id and title
        if IBaseObject.providedBy(self.context):
            for fieldname in ['id', 'title']:
                field = self.context.Schema().getField(fieldname)
                if field is None:
                    continue

                method = field.getIndexAccessor(self.context)
                value = method()
                text = text.replace(value, '', 1)
        # other content (e.g. dexterity): remove title
        elif IContentish.providedBy(self.context):
            text = text.replace(self.context.Title(), '', 1)

        # Strip html tags
        text = re.sub('<[^<]+?>', '', text)

        return text
