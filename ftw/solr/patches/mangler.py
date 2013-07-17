from zope.component import queryUtility
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.mangler import sort_aliases


# Allow more solr parameters
# e.g. 'qt'
def extractQueryParameters(args):
    """ extract parameters related to sorting and limiting search results
        from a given set of arguments, also removing them """
    def get(name):
        for prefix in 'sort_', 'sort-':
            key = '%s%s' % (prefix, name)
            value = args.get(key, None)
            if value is not None:
                del args[key]
                return value
        return None
    params = {}
    index = get('on')
    if index:
        reverse = get('order') or ''
        reverse = reverse.lower() in ('reverse', 'descending')
        order = reverse and 'desc' or 'asc'
        params['sort'] = '%s %s' % (index, order)
    limit = get('limit')
    if limit:
        params['rows'] = int(limit)
    for key, value in args.items():
        if key in ('fq', 'fl', 'facet', 'qt'):
            params[key] = value
            del args[key]
        elif key.startswith('facet.') or key.startswith('facet_'):
            name = lambda facet: facet.split(':', 1)[0]
            if isinstance(value, list):
                value = map(name, value)
            elif isinstance(value, tuple):
                value = tuple(map(name, value))
            else:
                value = name(value)
            params[key.replace('_', '.', 1)] = value
            del args[key]
        elif key == 'b_start':
            params['start'] = int(value)
            del args[key]
        elif key == 'b_size':
            params['rows'] = int(value)
            del args[key]

    # Add default search handler if no search handler is specified in the 
    # query. With Solr 4 we have to disable the /select search handler to be
    # able to select another search handler with the 'qt' parameter. However
    # queries without a 'qt' parameter do no longer work.
    # TODO: In the future we should extend c.solr to handle multiple search
    # handlers by URL.
    if 'qt' not in params:
        params['qt'] = 'select'

    return params

# Remove facet.field parameters specifying an non-existing field.
def cleanupQueryParameters(args, schema):
    """ validate and possibly clean up the given query parameters using
        the given solr schema """
    sort = args.get('sort', None)
    if sort is not None:
        field, order = sort.split(' ', 1)
        if not field in schema:
            field = sort_aliases.get(field, None)
        fld = schema.get(field, None)
        if fld is not None and fld.indexed:
            args['sort'] = '%s %s' % (field, order)
        else:
            del args['sort']

    # Remove facet fields that are not in the solr schema
    facet_fields = args.get('facet.field', [])
    if not isinstance(facet_fields, list):
        facet_fields = [facet_fields]
    valid_facet_fields = []
    for facet_field in facet_fields:
        fld = schema.get(facet_field, None)
        if fld is not None and fld.indexed:
            valid_facet_fields.append(facet_field)
    if valid_facet_fields:
        args['facet.field'] = valid_facet_fields
    elif 'facet.field' in args:
        del args['facet.field']

    if 'facet.field' in args and not 'facet' in args:
        args['facet'] = 'true'

    return args


# Do not extend params['fq'] if it is a list as this would end
# in the request.
def optimizeQueryParameters(query, params):
    """ optimize query parameters by using filter queries for
        configured indexes """
    config = queryUtility(ISolrConnectionConfig)
    fq = []
    if config is not None:
        for idxs in config.filter_queries:
            idxs = set(idxs.split(' '))
            if idxs.issubset(query.keys()):
                fq.append(' '.join([query.pop(idx) for idx in idxs]))
    if 'fq' in params:
        if isinstance(params['fq'], list):
            params['fq'] = params['fq'] + fq
        else:
            params['fq'] = [params['fq']] + fq
    elif fq:
        params['fq'] = fq
    if not query:
        query['*'] = '*:*'      # catch all if no regular query is left...
