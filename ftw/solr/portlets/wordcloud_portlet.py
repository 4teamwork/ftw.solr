from Acquisition import aq_inner
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import schema
from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import implements
from ftw.solr import _


class IWordCloudPortlet(IPortletDataProvider):
    """A WordCloud portlet.

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    portlet_title = schema.TextLine(
        title=_(u'label_portlet_title', default=u"Title"),
        description=_(u'help_portlet_title', default=u"Portlet title"),
        required=False,
        default=u"Word Cloud")

    num_words = schema.Int(
        title=_(u'label_num_words', default=u"Number of words"),
        description=_(u'help_num_words',
                      default=u"Maximum number of words to be displayed"),
        required=True,
        default=10)

    num_sizes = schema.Int(
        title=_(u'label_num_sizes', u"Number of sizes"),
        description=_(u'help_num_sizes',
                      default=u"Number of different sizes to represent term "
                               "weight"),
        required=True,
        default=5)

    scale_factor = schema.Float(
        title=_(u'label_scale_factor', default=u"Scale factor"),
        description=_(u'help_scale_factor',
                      default=u"Constant scaling factor to scale font size by"),
        required=True,
        default=2.0)


class Assignment(base.Assignment):
    """Portlet assignment for the Word Cloud portlet.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IWordCloudPortlet)

    def __init__(self, num_words, num_sizes, portlet_title, scale_factor):
        self.portlet_title = portlet_title
        self.num_words = num_words
        self.num_sizes = num_sizes
        self.scale_factor = scale_factor

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        'manage portlets' screen.

        Note: This is different from the `portlet_title` which, if set,
        will be displayed in the portlet header.
        """
        return "Word Cloud"


class Renderer(base.Renderer):
    """Portlet renderer for the Word Cloud portlet.

    This is registered in configure.zcml. The referenced page template only
    contains the basic portlet structure, the actual word cloud is rendered
    in the render_cloud() method by looking up the `wordcloud` browser view.
    """

    render = ViewPageTemplateFile('wordcloud_portlet.pt')

    def header(self):
        portlet_title = getattr(self.data, 'portlet_title', None)
        return portlet_title

    @property
    def available(self):
        return True

    def render_cloud(self):
        context = aq_inner(self.context)
        word_cloud_view = getMultiAdapter((context, self.request),
                                          name='wordcloud')

        num_words = getattr(self.data, 'num_words', None)
        num_sizes = getattr(self.data, 'num_sizes', None)
        scale_factor = getattr(self.data, 'scale_factor', None)

        kwargs = {'num_words': num_words,
                  'num_sizes': num_sizes,
                  'scale_factor': scale_factor}

        return word_cloud_view(**kwargs)


class AddForm(base.AddForm):
    """Portlet add form for the Word Cloud portlet.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IWordCloudPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IWordCloudPortlet)
