from Products.CMFCore.utils import getToolByName
from ftw.solr.converters import CONVERTERS
from ftw.solr.interfaces import ISolrIndexHandler
from logging import getLogger
from plone.indexer.interfaces import IIndexableObject
from plone.namedfile.interfaces import INamedBlobFile
from plone.rfc822.interfaces import IPrimaryFieldInfo
from zope.component import queryMultiAdapter
from zope.interface import implementer


logger = getLogger('ftw.solr.handlers')


@implementer(ISolrIndexHandler)
class DefaultIndexHandler(object):

    def __init__(self, context, manager):
        self.context = context
        self.manager = manager

    def add(self, attributes):
        conn = self.manager.connection
        if conn is None:
            return

        schema = self.manager.schema
        if not schema:
            logger.warning(
                'Unable to fetch schema, skipping indexing of %r',
                self.context)
            return

        unique_key = schema.unique_key
        if unique_key is None:
            logger.warning(
                'Schema is missing unique key, skipping indexing of %r',
                self.context)
            return

        data = self.get_data(attributes)

        if unique_key not in data:
            logger.warning(
                'Object is missing unique key, skipping indexing of %r',
                self.context)
            return

        # Atomic update: add set modifier except for unique key
        if attributes:
            id_ = data[unique_key]
            data = {k: {'set': v} for k, v in data.items() if k != unique_key}
            data[unique_key] = id_

        conn.add(data)

    def delete(self):
        conn = self.manager.connection
        if conn is None:
            return

        schema = self.manager.schema
        if not schema:
            logger.warning(
                'Unable to fetch schema, skipping unindexing of %r',
                self.context)
            return

        unique_key = schema.unique_key
        if unique_key is None:
            logger.warning(
                'Schema is missing unique key, skipping unindexing of %r',
                self.context)
            return

        data = self.get_data([unique_key])
        if unique_key not in data:
            logger.warning(
                'Object is missing unique key, skipping unindexing of %r',
                self.context)

        conn.delete(data[unique_key])

    def get_data(self, attributes):
        if not IIndexableObject.providedBy(self.context):
            catalog = getToolByName(self.context, 'portal_catalog')
            wrapped = queryMultiAdapter(
                (self.context, catalog), IIndexableObject,
                default=self.context)
        else:
            wrapped = self.context

        schema = self.manager.schema
        if attributes is None:
            attributes = set(schema.fields.keys())
        else:
            attributes = set(schema.fields.keys()).intersection(attributes)
        if schema.unique_key not in attributes:
            attributes.add(schema.unique_key)

        data = {}
        for name in attributes:
            if name.startswith('_'):
                continue
            if name == 'path':
                value = '/'.join(self.context.getPhysicalPath())
            else:
                try:
                    value = getattr(wrapped, name)
                    if callable(value):
                        value = value()
                except (AttributeError, TypeError):
                    continue

            if value is None:
                continue
            field_class = schema.field_types[
                schema.fields[name][u'type']][u'class']
            multivalued = schema.fields[name].get(u'multiValued', False)
            converter = CONVERTERS.get(field_class)
            if converter is not None:
                value = converter(value, multivalued)
            data[name] = value

        return data


@implementer(ISolrIndexHandler)
class ATBlobFileIndexHandler(DefaultIndexHandler):

    def add(self, attributes):
        conn = self.manager.connection
        if conn is None:
            return

        if attributes and 'SearchableText' not in attributes:
            return super(ATBlobFileIndexHandler, self).add(attributes)

        schema = self.manager.schema
        if not schema:
            logger.warning(
                'Unable to fetch schema, skipping indexing of %r',
                self.context)
            return

        if attributes is None:
            attributes = schema.fields.keys()
        attributes.remove('SearchableText')

        data = self.get_data(attributes)
        field = self.context.getPrimaryField()
        blob = field.get(self.context).blob

        conn.extract(blob, data)


@implementer(ISolrIndexHandler)
class DexterityItemIndexHandler(DefaultIndexHandler):

    def add(self, attributes):
        conn = self.manager.connection
        if conn is None:
            return

        try:
            info = IPrimaryFieldInfo(self.context, None)
        except TypeError:
            info = None
        if info is not None and INamedBlobFile.providedBy(info.value):
            blob = info.value._blob
        else:
            return super(DexterityItemIndexHandler, self).add(attributes)

        if attributes and 'SearchableText' not in attributes:
            return super(DexterityItemIndexHandler, self).add(attributes)

        schema = self.manager.schema
        if not schema:
            logger.warning(
                'Unable to fetch schema, skipping indexing of %r',
                self.context)
            return
        if attributes is None:
            attributes = schema.fields.keys()
        attributes.remove('SearchableText')

        data = self.get_data(attributes)
        conn.extract(blob, data)
