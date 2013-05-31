from zope.component import queryUtility
from collective.solr.interfaces import ISolrConnectionConfig


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
    return params


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
