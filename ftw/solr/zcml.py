# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope import schema
from zope.component.zcml import utility
from ftw.solr.interfaces import ISolrConnectionConfig
from ftw.solr.connection import SolrConnectionConfig


class ISolrConnectionConfigDirective(Interface):
    """Directive which registers a Solr connection config"""

    host = schema.ASCIILine(
        title=u"Host",
        description=u"The host name of the Solr instance to be used.",
        required=True,
    )

    port = schema.Int(
        title=u"Port",
        description=u"The port of the Solr instance to be used.",
        required=True,
    )

    base = schema.ASCIILine(
        title=u"Base",
        description=u"The base prefix of the Solr instance to be used "
                    "(e.g. /solr/corename or /api/cores/corename)",
        required=True,
    )


def solr_connection_config_directive(_context, host, port, base):

    utility(_context,
            provides=ISolrConnectionConfig,
            component=SolrConnectionConfig(host, port, base))
