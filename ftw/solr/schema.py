

class SolrSchema(object):

    def __init__(self, manager):
        self.manager = manager
        self.retrieve()

    def retrieve(self):
        """Retrieve the Solr schema"""
        conn = self.manager.connection
        if conn is None:
            schema = {}
        else:
            resp = conn.get('/schema')
            schema = resp.get(u'schema', {})
        self.unique_key = schema.get(u'uniqueKey')
        self.name = schema.get(u'name')
        self.version = schema.get(u'version')
        self.fields = {}
        for field in schema.get(u'fields', []):
            self.fields[field[u'name']] = field
        self.copy_fields = {}
        for field in schema.get(u'copyFields', []):
            self.copy_fields[field[u'dest']] = field
        self.dynamic_fields = {}
        for field in schema.get(u'dynamicFields', []):
            self.dynamic_fields[field[u'name']] = field
        self.field_types = {}
        for ftype in schema.get(u'fieldTypes', []):
            self.field_types[ftype[u'name']] = ftype

    def __nonzero__(self):
        if self.unique_key is not None:
            return True
        return False

    def field_class(self, name):
        return self.field_types.get(
                self.fields.get(name, {}).get(u'type'), {}).get(u'class')
