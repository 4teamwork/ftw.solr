from zope.component import getMultiAdapter
from zope.interface import Interface
from plone.indexer import indexer
from Products.CMFCore.utils import getToolByName
from ZODB.POSException import ConflictError


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
def searchable_text(obj, **kwargs):
    """A SearchableText indexer that does not include id, title and 
       description.
    """
    data = []
    charset = obj.getCharset()
    for field in obj.Schema().fields():
        if not field.searchable:
            continue
        if field.getName() in ['id', 'title', 'description', 'searchwords']:
            continue
        method = field.getIndexAccessor(obj)
        try:
            datum =  method(mimetype="text/plain")
        except TypeError:
            # Retry in case typeerror was raised because accessor doesn't
            # handle the mimetype argument
            try:
                datum =  method()
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                continue
        if datum:
            vocab = field.Vocabulary(obj)
            if isinstance(datum, (list, tuple)):
                # Unmangle vocabulary: we index key AND value
                vocab_values = map(lambda value, vocab=vocab: vocab.getValue(value, ''), datum)
                datum = list(datum)
                datum.extend(vocab_values)
                datum = ' '.join(datum)
            elif isinstance(datum, basestring):
                if isinstance(datum, unicode):
                    datum = datum.encode(charset)
                value = vocab.getValue(datum, '')
                if isinstance(value, unicode):
                    value = value.encode(charset)
                datum = "%s %s" % (datum, value, )

            if isinstance(datum, unicode):
                datum = datum.encode(charset)
            data.append(str(datum))

    data = ' '.join(data)
    return data
