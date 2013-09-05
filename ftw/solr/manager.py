from collective.solr import manager
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.solr import SolrConnection
from collective.solr.local import getLocal, setLocal
from ftw.solr.interfaces import IZCMLSolrConnectionConfig
from logging import getLogger
from zope.component import getUtility, queryUtility
from zope.interface import implements
from collective.solr.parser import SolrField


logger = getLogger('ftw.solr.manager')


class ZCMLSolrConnectionConfig(object):
    implements(IZCMLSolrConnectionConfig)
    def __init__(self, host, port, base):
        self.host = '%s:%d' % (host, port)
        self.base = base


class FtwSolrConnection(SolrConnection):

    def get_schema(self):
        """Memoized access to Solr Schema.

        We need to know which one is the uniqueKey in the add() method below,
        but don't want to hit Solr with a request for the schema on every
        single add().
        """
        if not hasattr(self, '_schema'):
            self._schema = self.getSchema()
        return self._schema

    def add(self, boost_values=None, **fields):
        """
        Modified variant of the original SolrConnection.add() that uses atomic
        updates and only updates the specified fields for a document in Solr.

        If the document doesn't exist yet, it will be added, so this should
        work as a drop-in replacement of the original add().

        The main difference to the original method is that we set the
        update="set" attribute on each field except the uniqueKey.
        """
        schema = self.get_schema()

        # Warn about fields that aren't stored
        for key in schema.keys():
            field = schema[key]
            if isinstance(field, SolrField) and field.get('stored') != True:
                logger.warn("Field '%s' is not stored! It will be dropped "
                            "from the document upon updates!" % key)

        uniqueKey = schema.get('uniqueKey', None)
        if uniqueKey is None:
            raise Exception("Could not get uniqueKey from Solr schema")

        if not uniqueKey in fields.keys():
            logger.warn("uniqueKey '%s' missing for item %s, skipping" %
                        (uniqueKey, fields))
            return

        within = fields.pop('commitWithin', None)
        if within:
            lst = ['<add commitWithin="%s">' % str(within)]
        else:
            lst = ['<add>']
        if boost_values is None:
            boost_values = {}
        if '' in boost_values:      # boost value for the entire document
            lst.append('<doc boost="%s">' % boost_values[''])
        else:
            lst.append('<doc>')
        for f, v in fields.items():
            if f == uniqueKey:
                # uniqueKey is needed to identify the document to be updated
                # and therefore *must not* have the update="set" attribute
                tmpl = '<field name="%s">%%s</field>' % self.escapeKey(f)
                lst.append(tmpl % self.escapeVal(v))
                continue

            if f in boost_values:
                tmpl = '<field name="%s" boost="%s" update="set">%%s</field>' % (
                    self.escapeKey(f), boost_values[f])
            else:
                tmpl = '<field name="%s" update="set">%%s</field>' % self.escapeKey(f)
            if isinstance(v, (list, tuple)):   # multi-valued
                for value in v:
                    lst.append(tmpl % self.escapeVal(value))
            else:
                lst.append(tmpl % self.escapeVal(v))
        lst.append('</doc>')
        lst.append('</add>')
        xstr = '\n'.join(lst)

        if self.conn.debuglevel > 0:
            logger.info('Update message:\n' + xstr)
        return self.doUpdateXML(xstr)


class SolrConnectionManager(manager.SolrConnectionManager):
    """Connection manager that allows for connection configuration via ZCML
    and uses our custom FtwSolrConnection that enables atomic updates.
    """

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
                conn = FtwSolrConnection(host=zcmlconfig.host,
                                         solrBase=zcmlconfig.base,
                                         persistent=True)
                setLocal('connection', conn)

        # Open connection defined in control panel if we don't have one yet.
        if conn is None and config.host is not None:
            host = '%s:%d' % (config.host, config.port)
            logger.debug('opening connection to %s', host)
            conn = FtwSolrConnection(host=host, solrBase=config.base,
                                     persistent=True)
            setLocal('connection', conn)
        return conn
