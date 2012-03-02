from zope.component import queryUtility
from collective.solr.interfaces import ISolrConnectionConfig

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
