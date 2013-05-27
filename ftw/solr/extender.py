from archetypes.schemaextender.interfaces import ISchemaExtender
from collective.solr import extender
from ftw.solr import _
from Products.Archetypes.atapi import BooleanWidget
from Products.Archetypes.atapi import TextAreaWidget
from zope.interface import implements


class SearchExtender(object):
    """Adapter that adds search metadata."""

    implements(ISchemaExtender)

    _fields = [
        extender.ExtensionBooleanField(
            'showinsearch',
            languageIndependent=True,
            schemata='settings',
            default=True,
            write_permission='ftw.solr: Edit search settings',
            widget=BooleanWidget(
                label=_(u'label_showinsearch',
                        default=u'Show in search'),
                visible={"edit": "visible", "view": "invisible"},
                description="",
                )),

        extender.ExtentionTextField(
            'searchwords',
            searchable=False,
            schemata='settings',
            languageIndependent=False,
            write_permission='ftw.solr: Edit search settings',
            allowable_content_types = 'text/plain',
            widget=TextAreaWidget(
                label=_(u'label_searchwords', default=u'Search words'),
                description=_(
                    u'help_searchwords',
                    default=u'Specify words for which this item will show up '
                    'as the first search result. Multiple words can be '
                    'specified on new lines.'),
                visible={"edit": "visible", "view": "invisible"},
                )),
        ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self._fields
