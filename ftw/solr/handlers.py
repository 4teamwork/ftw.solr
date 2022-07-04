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
        if self.manager.connection is None:
            return

        error = self.get_schema_error()
        if error:
            logger.warning('%s, skipping indexing of %r', error, self.context)
            return

        data = self.get_data(attributes)

        unique_key = self.manager.schema.unique_key
        if unique_key not in data:
            logger.warning(
                'Object is missing unique key, skipping indexing of %r',
                self.context)
            return

        if attributes:
            self.unset_lang_fields(attributes, data)
            data = self.add_atomic_update_modifier(data, unique_key)

        if data:
            self.manager.connection.add(data)

    def delete(self):
        if self.manager.connection is None:
            return

        error = self.get_schema_error()
        if error:
            logger.warning(
                '%s, skipping unindexing of %r', error, self.context)
            return

        unique_key = self.manager.schema.unique_key
        data = self.get_data([unique_key])
        if unique_key not in data:
            logger.warning(
                'Object is missing unique key, skipping unindexing of %r',
                self.context)
            return

        self.manager.connection.delete(data[unique_key])

    def get_data(self, attributes):
        if not IIndexableObject.providedBy(self.context):
            catalog = getToolByName(self.context, 'portal_catalog')
            wrapped = queryMultiAdapter(
                (self.context, catalog), IIndexableObject,
                default=self.context)
        else:
            wrapped = self.context

        schema = self.manager.schema
        if not attributes:
            attributes = self.all_indexable_fields()
        else:
            attributes = self.all_indexable_fields().intersection(attributes)

        if schema.unique_key not in attributes:
            attributes.add(schema.unique_key)

        # If path gets (re)indexed, we also need to (re)index path_depth
        # in Solr. Because path_depth is not a catalog index, we would
        # otherwise fail to update it in cases where a specific list of
        # `idxs` including path is passed to reindexObject().
        if 'path' in attributes and 'path_depth' in schema.fields:
            attributes.add('path_depth')

        data = {}
        for name in attributes:
            if name.startswith('_'):
                continue
            if name == 'path':
                value = '/'.join(self.context.getPhysicalPath())
            elif name == 'path_depth':
                value = len(self.context.getPhysicalPath()) - 1
            else:
                try:
                    value = getattr(wrapped, name)
                    if callable(value):
                        value = value()
                except (AttributeError, TypeError):
                    continue

            field_class = schema.field_types[
                schema.fields[name][u'type']][u'class']
            multivalued = schema.fields[name].get(u'multiValued', False)
            converter = CONVERTERS.get(field_class)
            if converter is not None:
                value = converter(value, multivalued)
            data[name] = value

        return data

    def get_schema_error(self):
        if not self.manager.schema:
            return 'Unable to fetch schema'

        if self.manager.schema.unique_key is None:
            return 'Schema is missing unique key'

    def add_atomic_update_modifier(self, data, unique_key):
        id_ = data[unique_key]
        data = {k: {'set': v} for k, v in data.items() if k != unique_key}
        if not data:
            return
        data[unique_key] = id_
        return data

    def unset_lang_fields(self, attributes, data):
        unset_lang_fields = {}
        for field in self.manager.config.langid_fields:
            if field in attributes:
                unset_lang_fields.update({
                    '{}_{}'.format(field, lang): {'set': None}
                    for lang in self.manager.config.langid_langs
                })
        if unset_lang_fields:
            unique_key = self.manager.schema.unique_key
            unset_lang_fields[unique_key] = data[unique_key]
            self.manager.connection.add(unset_lang_fields)

    def all_indexable_fields(self):
        return (
            set(self.manager.schema.fields.keys())
            - set(self.manager.config.langid_langfields)
        )


@implementer(ISolrIndexHandler)
class ATBlobFileIndexHandler(DefaultIndexHandler):

    def add(self, attributes):
        if self.manager.connection is None:
            return

        if isinstance(attributes, tuple):
            attributes = list(attributes)

        error = self.get_schema_error()
        if error:
            logger.warning('%s, skipping indexing of %r', error, self.context)
            return

        if attributes is None:
            attributes = self.all_indexable_fields()

        extract = False
        if 'SearchableText' in attributes:
            attributes.remove('SearchableText')
            extract = True

        unique_key = self.manager.schema.unique_key
        raw_data = self.get_data(attributes)

        if attributes:
            self.unset_lang_fields(attributes, raw_data)
            data = self.add_atomic_update_modifier(raw_data, unique_key)
            if data:
                self.manager.connection.add(data)

        if extract:
            self.unset_lang_fields(['SearchableText'], raw_data)
            field = self.context.getPrimaryField()
            blob = field.get(self.context).blob
            content_type = field.get(self.context).getContentType()
            self.manager.connection.extract(
                blob, 'SearchableText', {unique_key: raw_data[unique_key]},
                content_type)


@implementer(ISolrIndexHandler)
class DexterityItemIndexHandler(DefaultIndexHandler):

    def add(self, attributes):
        if self.manager.connection is None:
            return

        if isinstance(attributes, tuple):
            attributes = list(attributes)

        error = self.get_schema_error()
        if error:
            logger.warning('%s, skipping indexing of %r', error, self.context)
            return

        blob = None
        content_type = None
        try:
            info = IPrimaryFieldInfo(self.context, None)
        except TypeError:
            info = None
        if info is not None and INamedBlobFile.providedBy(info.value):
            blob = info.value._blob
            content_type = info.value.contentType

        if not attributes:
            attributes = self.all_indexable_fields()

        extract = False
        if 'SearchableText' in attributes and blob is not None:
            attributes.remove('SearchableText')
            extract = True

        unique_key = self.manager.schema.unique_key
        raw_data = self.get_data(attributes)

        if attributes:
            self.unset_lang_fields(attributes, raw_data)
            data = self.add_atomic_update_modifier(raw_data, unique_key)
            if data:
                self.manager.connection.add(data)

        if extract:
            self.unset_lang_fields(['SearchableText'], raw_data)
            self.manager.connection.extract(
                blob, 'SearchableText', {unique_key: raw_data[unique_key]},
                content_type)
