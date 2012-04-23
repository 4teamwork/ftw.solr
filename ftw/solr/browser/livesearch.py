from Acquisition import aq_inner
from zope.publisher.browser import BrowserView
from zope.i18n import translate
from zope.component import getMultiAdapter
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.utils import safe_unicode
from Products.PythonScripts.standard import url_quote_plus
from Products.PythonScripts.standard import html_quote

# SIMPLE CONFIGURATION
USE_ICON = True
MAX_TITLE = 29
MAX_DESCRIPTION = 93


legend_livesearch = _('legend_livesearch', default='LiveSearch &#8595;')
label_no_results_found = _('label_no_results_found', default='No matching results found.')
label_advanced_search = _('label_advanced_search', default='Advanced Search&#8230;')
label_show_all = _('label_show_all', default='Show all items')


class LiveSearchReplyView(BrowserView):
    """
    """
    def __init__(self, context, request):
        super(LiveSearchReplyView, self).__init__(context, request)
        self.output = []

    def __call__(self):
        context = aq_inner(self.context)
        q = self.request.form.get('q', None)
        limit = int(self.request.form.get('limit', 10))
        path = self.request.form.get('path', None)

        plone_utils = getToolByName(context, 'plone_utils')
        pretty_title_or_id = plone_utils.pretty_title_or_id
        plone_view = getMultiAdapter((context, self.request), name='plone')

        pprops = getToolByName(context, 'portal_properties')
        sprops = getattr(pprops, 'site_properties', None)
        useViewAction = []
        if sprops is not None:
            useViewAction = sprops.getProperty('typesUseViewActionInListings',
                                               [])

        # XXX really if it contains + * ? or -
        # it will not be right since the catalog ignores all non-word
        # characters equally like
        # so we don't even attept to make that right.
        # But we strip these and these so that the catalog does
        # not interpret them as metachars
        # See http://dev.plone.org/plone/ticket/9422 for an explanation of '\u3000'
        multispace = u'\u3000'.encode('utf-8')
        for char in ('?', '-', '+', '*', multispace):
            q = q.replace(char, ' ')
        r = quote_bad_chars(q)+'*'
        searchterms = url_quote_plus(r)

        
        site_encoding = plone_utils.getSiteEncoding()
        if path is None:
            path = getNavigationRoot(context)
        catalog = getToolByName(context, 'portal_catalog')
        friendly_types = plone_utils.getUserFriendlyTypes()
        results = catalog(SearchableText=r, portal_type=friendly_types,
                          path=path, sort_limit=limit)

        searchterm_query = '?searchterm=%s'%url_quote_plus(q)
        if not results:
            self.write('''<fieldset class="livesearchContainer">''')
            self.write('''<legend id="livesearchLegend">%s</legend>''' % (
                translate(legend_livesearch, context=self.request)))
            self.write('''<div class="LSIEFix">''')
            self.write('''<div id="LSNothingFound">%s</div>''' % (
                translate(label_no_results_found, context=self.request)))
            self.write('''<div class="LSRow">''')
            self.write('<a href="search_form" style="font-weight:normal">%s</a'
                '>' % translate(label_advanced_search, context=self.request))
            self.write('''</div>''')
            self.write('''</div>''')
            self.write('''</fieldset>''')

        else:
            self.write('''<fieldset class="livesearchContainer">''')
            self.write('''<legend id="livesearchLegend">%s</legend>''' % (
                translate(legend_livesearch, context=self.request)))
            self.write('''<div class="LSIEFix">''')
            self.write('''<ul class="LSTable">''')

            for result in results[:limit]:

                icon = plone_view.getIcon(result)
                itemUrl = result.getURL()
                if result.portal_type in useViewAction:
                    itemUrl += '/view'
                itemUrl = itemUrl + searchterm_query

                self.write('''<li class="LSRow">''')
                self.write(icon.html_tag() or '')
                full_title = safe_unicode(pretty_title_or_id(result))
                if len(full_title) > MAX_TITLE:
                    display_title = ''.join((full_title[:MAX_TITLE], '...'))
                else:
                    display_title = full_title
                full_title = full_title.replace('"', '&quot;')
                klass = 'contenttype-%s' % plone_utils.normalizeString(result.portal_type)
                self.write('''<a href="%s" title="%s" class="%s">%s</a>''' % (itemUrl, full_title, klass, display_title))
                display_description = safe_unicode(result.Description)
                if len(display_description) > MAX_DESCRIPTION:
                    display_description = ''.join((display_description[:MAX_DESCRIPTION], '...'))
                # need to quote it, to avoid injection of html containing javascript and other evil stuff
                display_description = html_quote(display_description)
                self.write('''<div class="LSDescr">%s</div>''' % (display_description))
                self.write('''</li>''')
                full_title, display_title, display_description = None, None, None

            if len(results)>limit:
                facet_params = context.restrictedTraverse('@@search-facets/facet_parameters')()
                # add a more... row
                self.write('''<li class="LSRow">''')
                self.write('<a href="%s&%s" style="font-weight:normal">%s</a>' % ('search?SearchableText=' + searchterms, facet_params, translate(label_show_all, context=self.request)))
                self.write('''</li>''')
            self.write('''</ul>''')
            self.write('''</div>''')
            self.write('''</fieldset>''')

        self.request.response.setHeader('Content-Type', 'text/xml;charset=%s' % site_encoding)
        return '\n'.join(self.output).encode(site_encoding)

    def write(self, s):
        self.output.append(safe_unicode(s))


def quotestring(s):
    return '"%s"' % s

def quote_bad_chars(s):
    bad_chars = ["(", ")"]
    for char in bad_chars:
        s = s.replace(char, quotestring(char))
    return s
