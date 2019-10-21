from ftw.solr import _
from ftw.solr import IS_PLONE_5
from zope import schema
from zope.interface import Interface


layerinterface = Interface
if IS_PLONE_5:
    from collective.solr.browser.interfaces import IThemeSpecific
    layerinterface = IThemeSpecific


class IFtwSolrLayer(layerinterface):
    """Browser layer for ftw.solr
    """


class ILiveSearchSettings(Interface):

    grouping = schema.Bool(
        title=_(u'Enable Grouping in LiveSearch'),
        description=_(u'If enabled, livesearch results are grouped by portal '
                       'type.'),
        default=False,
    )

    group_by = schema.List(
        title=_(u'Groups'),
        description=_(u'Specify a list of portal types by which livesearch '
                       'results are grouped. Groups are shown in the provided '
                       'order. Results that do not match a portal type in the '
                       'given list are shown at the bottom.'),
        default=[u'Folder', u'Document', u'News Item', u'Event', u'File',
                 u'Image'],
        value_type=schema.TextLine(),
        required=False,
    )

    group_search_limit = schema.Int(
        title=_(u'Group Search Limit'),
        description=_(u'The maximum number of search results to consider for'
                       'grouping.'),
        default=1000,
    )

    group_limit = schema.Int(
        title=_(u'Group Limit'),
        description=_(u'The maximum number of search results per group.'),
        default=7,
        required=False,
    )


    max_title = schema.Int(
        title=_(u'Maximum Title Length'),
        default=40,
    )

    max_description = schema.Int(
        title=_(u'Maximum Description Length'),
        default=100,
    )


class ISearchSettings(Interface):

    path_based_breadcrumbs = schema.Bool(
        title=_(u'Use Path for Breadcrumbs'),
        default=False,
    )

    max_breadcrumbs = schema.Int(
        title=_(u'Max. Breadcrumbs'),
        default=3,
    )

    respect_navroot = schema.Bool(
        title=_(u'Respect Navigation Root'),
        description=_(u'Constrain searches to navigation root'),
        default=False,
    )

class IZCMLSolrConnectionConfig(Interface):
    """Solr connection settings configured through ZCML.
    """
