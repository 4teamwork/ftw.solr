from Acquisition import aq_inner
from ZODB.POSException import ConflictError
from Products.ZCTextIndex.ParseTree import ParseError
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.navtree import getNavigationRoot
from zope.schema.interfaces import IVocabularyFactory
from zope.component import getUtility
from zope.publisher.browser import BrowserView


class QueryCatalogView(BrowserView):

    def querycatalog(self, REQUEST=None, show_all=0, quote_logic=0, 
                     quote_logic_indexes=['SearchableText',
                                          'Description','Title'],
                     use_types_blacklist=False, show_inactive=False,
                     use_navigation_root=False, b_start=None, b_size=None):


        context = aq_inner(self.context)
        results=[]
        catalog=context.portal_catalog
        vocab = getUtility(IVocabularyFactory, name='collective.solr.indexes')
        indexes = [i.token for i in vocab(context)]
        query={}
        show_query=show_all
        second_pass = {}

        if REQUEST is None:
            REQUEST = self.request

        # See http://dev.plone.org/plone/ticket/9422 for
        # an explanation of '\u3000'
        multispace = u'\u3000'.encode('utf-8')

        # Avoid creating a session implicitly.
        for k in REQUEST.keys():
            if k in ('SESSION',):
                continue
            v = REQUEST.get(k)
            if v and k in indexes:
                if k in quote_logic_indexes:
                    v = quote_bad_chars(v)
                    if multispace in v:
                        v = v.replace(multispace, ' ')
                    if quote_logic:
                        v = quotequery(v)
                query[k] = v
                show_query = 1
            elif k.endswith('_usage'):
                key = k[:-6]
                param, value = v.split(':')
                second_pass[key] = {param:value}
            elif k in ('sort_on', 'sort_order', 'sort_limit'):
                if k == 'sort_limit' and not isinstance(v, int):
                    query[k] = int(v)
                else:
                    query[k] = v
            elif k in ('fq', 'fl', 'facet', 'b_start', 'b_size', 'qt') or k.startswith('facet.'):
                query[k] = v

        for k, v in second_pass.items():
            qs = query.get(k)
            if qs is None:
                continue
            query[k] = q = {'query':qs}
            q.update(v)

        if b_start is not None:
            query['b_start'] = b_start
        if b_size is not None:
            query['b_size'] = b_size

        # doesn't normal call catalog unless some field has been queried
        # against. if you want to call the catalog _regardless_ of whether
        # any items were found, then you can pass show_all=1.
        if show_query:
            try:
                if use_types_blacklist:
                    self.ensureFriendlyTypes(query)
                if use_navigation_root:
                    self.rootAtNavigationRoot(query)
                query['show_inactive'] = show_inactive
                results = catalog(**query)
            except ParseError:
                pass

        return results

    def ensureFriendlyTypes(self, query):
        ploneUtils = getToolByName(self.context, 'plone_utils')
        portal_type = query.get('portal_type', [])
        if not isinstance(portal_type, list):
            portal_type = [portal_type]
        Type = query.get('Type', [])
        if not isinstance(Type, list):
            Type = [Type]
        typesList = portal_type + Type
        if not typesList:
            friendlyTypes = ploneUtils.getUserFriendlyTypes(typesList)
            query['portal_type'] = friendlyTypes

    def rootAtNavigationRoot(self, query):
        if 'path' not in query:
            query['path'] = getNavigationRoot(self.context)



def quotestring(s):
    return '"%s"' % s

def quotequery(s):
    if not s:
        return s
    try:
        terms = s.split()
    except ConflictError:
        raise
    except:
        return s
    tokens = ('OR', 'AND', 'NOT')
    s_tokens = ('OR', 'AND')
    check = (0, -1)
    for idx in check:
        if terms[idx].upper() in tokens:
            terms[idx] = quotestring(terms[idx])
    for idx in range(1, len(terms)):
        if (terms[idx].upper() in s_tokens and
            terms[idx-1].upper() in tokens):
            terms[idx] = quotestring(terms[idx])
    return ' '.join(terms)

# We need to quote parentheses when searching text indices (we use
# quote_logic_indexes as the list of text indices)
def quote_bad_chars(s):
    bad_chars = ["(", ")"]
    for char in bad_chars:
        s = s.replace(char, quotestring(char))
    return s
