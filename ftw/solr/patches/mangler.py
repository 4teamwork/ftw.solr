from AccessControl import getSecurityManager
from DateTime import DateTime
from zope.component import queryUtility
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.mangler import iso8601date
from collective.solr.mangler import sort_aliases, query_args, ignored, ranges
from collective.solr.queryparser import quote
from collective.solr.utils import prepare_wildcard
from ftw.solr.patches.utils import isSimpleTerm
from ftw.solr.patches.utils import isSimpleSearch


def strip_wildcards(value):
    return value.replace('*', '').replace('?', '')


def strip_parens(value):
    return value.strip('()')


def searchterms_from_value(value):
    """Turn a search query into a list of search terms, removing
    parentheses, wildcards and quoting any special characters.
    """
    # remove any parens and wildcards, so quote() doesn't try to escape them
    value = strip_wildcards(strip_parens(value))
    # then quote the value
    value = quote(value)
    # and again strip parentheses that might have been added by quote()
    value = strip_parens(value)
    return value.split()


def leading_wildcards(value):
    """Prepend wildcards to each term for a string of search terms.
    (foo bar baz) -> (*foo *bar *baz)
    """
    search_terms = searchterms_from_value(value)
    value = ' '.join(['*%s' % term for term in search_terms])
    return "(%s)" % prepare_wildcard(value)


def trailing_wildcards(value):
    """Append wildcards to each term for a string of search terms.
    (foo bar baz) -> (foo* bar* baz*)
    """
    search_terms = searchterms_from_value(value)
    value = ' '.join(['%s*' % term for term in search_terms])
    return "(%s)" % prepare_wildcard(value)


def mangle_searchable_text_query(value, pattern):
    value = value.lower()

    value_lwc = leading_wildcards(value)
    value_twc = trailing_wildcards(value)
    value = strip_wildcards(value)

    value = pattern.format(
        value=quote(value),
        value_lwc=value_lwc,
        value_twc=value_twc)
    return value


def mangleQuery(keywords, config, schema):
    """ translate / mangle query parameters to replace zope specifics
        with equivalent constructs for solr """
    extras = {}
    for key, value in keywords.items():
        if key.endswith('_usage'):          # convert old-style parameters
            category, spec = value.split(':', 1)
            extras[key[:-6]] = {category: spec}
            del keywords[key]
        elif isinstance(value, dict):       # unify dict parameters
            keywords[key] = value['query']
            del value['query']
            extras[key] = value
        elif hasattr(value, 'query'):       # unify object parameters
            keywords[key] = value.query
            extra = dict()
            for arg in query_args:
                arg_val = getattr(value, arg, None)
                if arg_val is not None:
                    extra[arg] = arg_val
            extras[key] = extra
        elif key in ignored:
            del keywords[key]

    # find EPI indexes
    if schema:
        epi_indexes = {}
        for name in schema.keys():
            parts = name.split('_')
            if parts[-1] in ['string', 'depth', 'parents']:
                count = epi_indexes.get(parts[0], 0)
                epi_indexes[parts[0]] = count + 1
        epi_indexes = [k for k, v in epi_indexes.items() if v == 3]
    else:
        epi_indexes = ['path']

    for key, value in keywords.items():
        args = extras.get(key, {})
        if key == 'SearchableText':
            pattern = getattr(config, 'search_pattern', '')
            if pattern and isSimpleSearch(value):
                value = mangle_searchable_text_query(value, pattern)
                keywords[key] = set([value])    # add literal query parameter
                continue
            elif isSimpleTerm(value): # use prefix/wildcard search
                keywords[key] = '(%s* OR %s)' % (
                    prepare_wildcard(value), value)
                continue
        if key in epi_indexes:
            path = keywords['%s_parents' % key] = value
            del keywords[key]
            if 'depth' in args:
                depth = int(args['depth'])
                if depth >= 0:
                    if not isinstance(value, (list, tuple)):
                        path = [path]
                    tmpl = '(+%s_depth:[%d TO %d] AND +%s_parents:%s)'
                    params = keywords['%s_parents' % key] = set()
                    for p in path:
                        base = len(p.split('/'))
                        params.add(tmpl % (key, base, base + depth, key, p))
                del args['depth']
        elif key == 'effectiveRange':
            if isinstance(value, DateTime):
                steps = getattr(config, 'effective_steps', 1)
                if steps > 1:
                    value = DateTime(value.timeTime() // steps * steps)
                value = iso8601date(value)
            del keywords[key]
            keywords['effective'] = '[* TO %s]' % value
            keywords['expires'] = '[%s TO *]' % value
        elif key == 'show_inactive':
            del keywords[key]           # marker for `effectiveRange`
        elif 'range' in args:
            if not isinstance(value, (list, tuple)):
                value = [value]
            payload = map(iso8601date, value)
            keywords[key] = ranges[args['range']] % tuple(payload)
            del args['range']
        elif 'operator' in args:
            if isinstance(value, (list, tuple)) and len(value) > 1:
                sep = ' %s ' % args['operator'].upper()
                value = sep.join(map(lambda item: '"'+str(item)+'"', map(iso8601date, value)))
                keywords[key] = '(%s)' % value
            del args['operator']
        elif key == 'allowedRolesAndUsers':
            if getattr(config, 'exclude_user', False):
                token = 'user$' + getSecurityManager().getUser().getId()
                if token in value:
                    value.remove(token)
        elif isinstance(value, DateTime):
            keywords[key] = iso8601date(value)
        elif not isinstance(value, basestring):
            assert not args, 'unsupported usage: %r' % args


# Allow more solr parameters
# e.g. 'qt'
def subtractQueryParameters(args, request_keywords=None):
    """ subtract parameters related to sorting and limiting search results
        from a given set of arguments, also removing them from the input """
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
