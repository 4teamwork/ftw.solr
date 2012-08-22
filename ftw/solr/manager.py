from collective.solr import manager
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.solr import SolrConnection
from collective.solr.local import getLocal, setLocal
from ftw.solr.interfaces import IZCMLSolrConnectionConfig
from logging import getLogger
from zope.component import getUtility, queryUtility
from zope.interface import implements

logger = getLogger('ftw.solr.manager')


class ZCMLSolrConnectionConfig(object):
    implements(IZCMLSolrConnectionConfig)
    def __init__(self, host, port, base):
        self.host = '%s:%d' % (host, port)
        self.base = base


class SolrConnectionManager(manager.SolrConnectionManager):

    def getConnection(self):
        """ returns an existing connection or opens one """
        config = getUtility(ISolrConnectionConfig)
        if not config.active:
            return None
        conn = getLocal('connection')

        # Try to open connection defined in zcml
        if conn is None:
            zcmlconfig = queryUtility(IZCMLSolrConnectionConfig)
            if zcmlconfig is not None:
                logger.debug('opening connection to %s', zcmlconfig.host)
                conn = SolrConnection(host=zcmlconfig.host,
                                      solrBase=zcmlconfig.base,
                                      persistent=True)
                setLocal('connection', conn)
        
        # Open connection defined in control panel if we don't have one yet.
        if conn is None and config.host is not None:
            host = '%s:%d' % (config.host, config.port)
            logger.debug('opening connection to %s', host)
            conn = SolrConnection(host=host, solrBase=config.base,
                persistent=True)
            setLocal('connection', conn)
        return conn