from ftw.solr import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.indexer import indexer
from plone.supermodel import model
from plone.supermodel.model import Schema
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope.i18nmessageid import MessageFactory
from zope.interface import alsoProvides
from zope.schema import Bool
from zope.schema import Text


_plone = MessageFactory('plone')


class IShowInSearch(Schema):
    """Behavior adding a "Show in search" checkbox in order to make
    it possible to exclude certain content from the search results.
    """

    model.fieldset(
        'settings',
        label=_plone(u'Settings'),
        fields=['showinsearch'])

    directives.write_permission(showinsearch='ftw.solr.EditSearchSettings')
    directives.omitted('showinsearch')
    directives.no_omit(IEditForm, 'showinsearch')
    directives.no_omit(IAddForm, 'showinsearch')
    showinsearch = Bool(
        title=_(u'label_showinsearch', default=u'Show in search'),
        description=u'',
        default=True)


alsoProvides(IShowInSearch, IFormFieldProvider)


class ISearchwords(Schema):
    """Adds a "Searchwords" field for adding additional search words
    the the search index for improving search results.
    """

    model.fieldset(
        'settings',
        label=_plone(u'Settings'),
        fields=['searchwords'])

    directives.write_permission(searchwords='ftw.solr.EditSearchSettings')
    directives.omitted('searchwords')
    directives.no_omit(IEditForm, 'searchwords')
    directives.no_omit(IAddForm, 'searchwords')
    searchwords = Text(
        title=_(u'label_searchwords', default=u'Search words'),
        description=_(u'help_searchwords',
                      default=u'Specify words for which this item will show up '
                      u'as the first search result. Multiple words can be '
                      u'specified on new lines.'),
        required=False)

alsoProvides(ISearchwords, IFormFieldProvider)


@indexer(ISearchwords)
def searchwords_indexer(obj):
    words = getattr(ISearchwords(obj), 'searchwords', '')
    if not isinstance(words, unicode):
        words = words.decode('utf-8')

    return filter(None,
                  [word.strip('\r ').lower() for word in words.split('\n')])
