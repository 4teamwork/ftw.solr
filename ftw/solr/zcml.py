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

    upload_blobs = schema.Bool(
        title=u"Upload Blobs",
        description=u"Upload blobs to extract handler via HTTP POST instead "
                    u"of making Solr retrieve them via filesystem.",
        default=False,
    )


def solr_connection_config_directive(_context, host, port, base, upload_blobs):

    utility(_context,
            provides=ISolrConnectionConfig,
            component=SolrConnectionConfig(host, port, base, upload_blobs))
