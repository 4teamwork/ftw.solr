from collective.solr.mangler import cleanupQueryParameters
from collective.solr.mangler import optimizeQueryParameters
from collective.solr.mangler import subtractQueryParameters
from collective.solr.queryparser import quote
from collective.solr.search import languageFilter
from collective.solr.utils import isWildCard
from collective.solr.utils import prepare_wildcard
from collective.solr.utils import prepareData
from ftw.solr.patches.mangler import mangleQuery
from logging import getLogger
from Missing import MV


logger = getLogger('collective.solr.search')


def buildQueryAndParameters(self, default=None, **args):
    """ helper to build a querystring for simple use-cases """
    schema = self.getManager().getSchema() or {}
    config = self.getConfig()

    params = subtractQueryParameters(args)
    params = cleanupQueryParameters(params, schema)

    languageFilter(args)
    prepareData(args)
    mangleQuery(args, config, schema)

    logger.debug('building query for "%r", %r', default, args)
    defaultSearchField = getattr(schema, 'defaultSearchField', None)

    if default is not None and defaultSearchField is not None:
        args[None] = default

    query = {}

    for name, value in sorted(args.items()):
        field = schema.get(name or defaultSearchField, None)
        if field is None or not field.indexed:
            logger.info(
                'dropping unknown search attribute "%s" '
                ' (%r) for query: %r', name, value, args
            )
            continue
        if isinstance(value, bool):
            value = str(value).lower()
        elif not value:     # solr doesn't like empty fields (+foo:"")
            if not name:
                continue
            logger.info(
                'empty search term form "%s:%s", aborting buildQuery' % (
                    name,
                    value
                )
            )
            return {}, params
        elif field.class_ == 'solr.BoolField':
            if not isinstance(value, (tuple, list)):
                value = [value]
            falses = '0', 'False', MV
            true = lambda v: bool(v) and v not in falses
            value = set(map(true, value))
            if not len(value) == 1:
                assert len(value) == 2      # just to make sure
                continue                    # skip when "true or false"
            value = str(value.pop()).lower()
        elif isinstance(value, (tuple, list)):
            # list items should be treated as literals, but
            # nevertheless only get quoted when necessary
            def quoteitem(term):
                if isinstance(term, unicode):
                    term = term.encode('utf-8')
                quoted = quote(term)
                if not quoted.startswith('"') and not quoted == term:
                    quoted = quote('"' + term + '"')
                return quoted
            value = '(%s)' % ' OR '.join(map(quoteitem, value))
        elif isinstance(value, set):        # sets are taken literally
            if len(value) == 1:
                query[name] = ''.join(value)
            else:
                query[name] = '(%s)' % ' OR '.join(value)
            if '/' in query[name]:
                query[name] = query[name].replace('/', '\\/')
            continue
        elif isinstance(value, basestring):
            if field.class_ == 'solr.TextField':
                if isWildCard(value):
                    value = prepare_wildcard(value)
                value = quote(value, textfield=True)
                # if we have an intra-word hyphen, we need quotes
                if '\\-' in value or '\\+' in value:
                    if value[0] != '"':
                        value = '"%s"' % value
            else:
                value = quote(value)
            if not value:   # don't search for empty strings, even quoted
                continue
        else:
            logger.info(
                'skipping unsupported value "%r" (%s)', value, name
            )
            continue
        if name is None:
            if value and value[0] not in '+-':
                value = '+%s' % value
        else:
            value = '+%s:%s' % (name, value)

        query[name] = value
    logger.debug('built query "%s"', query)

    if query:
        optimizeQueryParameters(query, params)
    return query, params
