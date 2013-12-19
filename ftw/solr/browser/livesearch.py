from Acquisition import aq_inner
from ftw.solr.interfaces import ILiveSearchSettings
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.utils import safe_unicode
from Products.PythonScripts.standard import html_quote
from Products.PythonScripts.standard import url_quote_plus
from zope.component import getMultiAdapter, getUtility
from zope.i18n import translate
from zope.publisher.browser import BrowserView

legend_livesearch = _('legend_livesearch', default='LiveSearch &#8595;')
label_no_results_found = _('label_no_results_found', default='No matching results found.')
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
        self.limit = int(self.request.form.get('limit', 10))
        path = self.request.form.get('path', None)

        plone_utils = getToolByName(context, 'plone_utils')
        self.pretty_title_or_id = plone_utils.pretty_title_or_id
        self.normalizeString = plone_utils.normalizeString
        plone_view = getMultiAdapter((context, self.request), name='plone')
        self.getIcon = plone_view.getIcon

        pprops = getToolByName(context, 'portal_properties')
        sprops = getattr(pprops, 'site_properties', None)
        self.useViewAction = []
        if sprops is not None:
            self.useViewAction = sprops.getProperty('typesUseViewActionInListings',
                                               [])

        registry = getUtility(IRegistry)
        self.settings = registry.forInterface(ILiveSearchSettings)

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
        self.searchterms = url_quote_plus(r)

        site_encoding = plone_utils.getSiteEncoding()
        if path is None:
            path = getNavigationRoot(context)
        catalog = getToolByName(context, 'portal_catalog')
        friendly_types = plone_utils.getUserFriendlyTypes()

        self.facet_params = context.restrictedTraverse('@@search-facets/facet_parameters')()

        if self.settings.grouping:
            results = catalog(SearchableText=r, portal_type=friendly_types,
                              qt='livesearch', path=path,
                              sort_limit=self.settings.group_search_limit)

            group_by_types = self.settings.group_by + ['other']
            grouped_results = {}
            for type_ in group_by_types:
                grouped_results[type_] = []

            for result in results[:self.settings.group_search_limit]:
                if result.portal_type in grouped_results:
                    grouped_results[result.portal_type].append(result)
                else:
                    grouped_results['other'].append(result)

        else:
            results = catalog(SearchableText=r, portal_type=friendly_types,
                              qt='livesearch', path=path,
                              sort_limit=self.limit)

        self.searchterm_query = '?searchterm=%s'%url_quote_plus(q)
        if not results:
            self.write('''<fieldset class="livesearchContainer">''')
            self.write('''<legend id="livesearchLegend">%s</legend>''' % (
                translate(legend_livesearch, context=self.request)))
            self.write('''<div class="LSIEFix">''')
            self.write('''<div id="LSNothingFound">%s</div>''' % (
                translate(label_no_results_found, context=self.request)))
            self.write('''</div>''')
            self.write('''</fieldset>''')

        else:
            self.write('''<fieldset class="livesearchContainer">''')
            self.write('''<legend id="livesearchLegend">%s</legend>''' % (
                translate(legend_livesearch, context=self.request)))
            self.write('''<div class="LSIEFix">''')

            if self.settings.grouping:
                self.write_grouped_results(grouped_results, group_by_types)
            else:
                self.write_results(results)

            self.write('''</div>''')
            self.write('''</fieldset>''')

        self.request.response.setHeader('Content-Type', 'text/xml;charset=%s' % site_encoding)
        return '\n'.join(self.output).encode(site_encoding)

    def write(self, s):
        self.output.append(safe_unicode(s))

    def write_results(self, results):
        self.write('''<ul class="LSTable">''')
        for result in results[:self.limit]:
            icon = self.getIcon(result)
            itemUrl = result.getURL()
            if result.portal_type in self.useViewAction:
                itemUrl += '/view'
            itemUrl = itemUrl + self.searchterm_query

            self.write('''<li class="LSRow">''')
            self.write(icon.html_tag() or '')
            full_title = safe_unicode(self.pretty_title_or_id(result))
            if len(full_title) > self.settings.max_title:
                display_title = ''.join((full_title[:self.settings.max_title], '...'))
            else:
                display_title = full_title
            full_title = full_title.replace('"', '&quot;')
            klass = 'contenttype-%s' % self.normalizeString(result.portal_type)
            self.write('''<a href="%s" title="%s" class="%s">%s</a>''' % (itemUrl, full_title, klass, display_title))
            display_description = safe_unicode(result.Description)
            if len(display_description) > self.settings.max_description:
                display_description = ''.join((display_description[:self.settings.max_description], '...'))
            # need to quote it, to avoid injection of html containing javascript and other evil stuff
            display_description = html_quote(display_description)
            self.write('''<div class="LSDescr">%s</div>''' % (display_description))
            self.write('''</li>''')
            full_title, display_title, display_description = None, None, None

        if len(results) > self.limit:
            # add a more... row
            self.write('''<li class="LSRow">''')
            self.write(self.get_show_more_link())
            self.write('''</li>''')
        self.write('''</ul>''')

    def write_grouped_results(self, grouped_results, group_by_types):
        show_more = False
        self.write('''<dl class="LSTable">''')
        for ptype in group_by_types:
            results = grouped_results[ptype]
            if results:
                self.write('''<dt class="LSGroup">%s</dt>''' % translate(ptype, domain="plone", context=self.request))
                for result in results[:self.settings.group_limit]:
                    icon = self.getIcon(result)
                    itemUrl = result.getURL()
                    if result.portal_type in self.useViewAction:
                        itemUrl += '/view'
                    itemUrl = itemUrl + self.searchterm_query

                    self.write('''<dd class="LSRow">''')
                    self.write(icon.html_tag() or '')
                    full_title = safe_unicode(self.pretty_title_or_id(result))
                    if len(full_title) > self.settings.max_title:
                        display_title = ''.join((full_title[:self.settings.max_title], '...'))
                    else:
                        display_title = full_title
                    full_title = full_title.replace('"', '&quot;')
                    klass = 'contenttype-%s' % self.normalizeString(result.portal_type)
                    self.write('''<a href="%s" title="%s" class="%s">%s</a>''' % (itemUrl, full_title, klass, display_title))
                    display_description = safe_unicode(result.Description)
                    if len(display_description) > self.settings.max_description:
                        display_description = ''.join((display_description[:self.settings.max_description], '...'))
                    # need to quote it, to avoid injection of html containing javascript and other evil stuff
                    display_description = html_quote(display_description)
                    self.write('''<div class="LSDescr">%s</div>''' % (display_description))
                    self.write('''</dd>''')
                if len(results) > self.settings.group_limit:
                    show_more = True

        if show_more:
            # add a more... row
            self.write('''<dd class="LSRow LSShowMore">''')
            self.write(self.get_show_more_link())
            self.write('''</dd>''')

        self.write('''</dl>''')

    def get_show_more_link(self):
        params = self.facet_params
        params += '&SearchableText=' + self.searchterms
        path = self.request.form.get('path', None)
        if path:
            params += '&path=' + url_quote_plus(path)

        return '<a href="@@search?%s" style="font-weight:normal">%s</a>' % (
            params,
            translate(label_show_all, context=self.request),
        )


def quotestring(s):
    return '"%s"' % s


def quote_bad_chars(s):
    bad_chars = ["(", ")"]
    for char in bad_chars:
        s = s.replace(char, quotestring(char))
    return s
