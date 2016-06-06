from ftw.solr import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.supermodel.model import Schema
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope.i18nmessageid import MessageFactory
from zope.interface import alsoProvides
from zope.schema import Bool


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
