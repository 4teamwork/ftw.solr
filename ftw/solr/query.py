from ftw.solr.converters import to_iso8601
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrSettings
from logging import getLogger
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from ZPublisher.HTTPRequest import record

import re

logger = getLogger('ftw.solr.query')

SPECIAL_CHARS = [
    '+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~',
    '*', '?', ':', '/']

OPERATORS = re.compile(r'(.*)\s+(AND|OR|NOT)\s+', re.UNICODE)


def escape(term):
    for char in SPECIAL_CHARS:
        term = term.replace(char, '\\' + char)
    return term


def is_simple_search(phrase):
    num_quotes = phrase.count('"')
    if num_quotes % 2 == 0:
        # Replace quoted parts with a marker
        # "foo bar" -> quoted
        parts = phrase.split('"')
        new_parts = []
        for i in range(0, len(parts)):
            if i % 2 == 0:
                new_parts.append(parts[i])
            else:
                new_parts.append('quoted')
        phrase = u''.join(new_parts)
    if bool(OPERATORS.match(phrase)):
        return False
    return True


def split_simple_search(phrase):
    parts = phrase.split('"')
    terms = []
    for i in range(0, len(parts)):
        if i % 2 == 0:
            # Unquoted text
            terms.extend([term for term in parts[i].split() if term])
        else:
            # The uneven parts are those inside quotes
            if parts[i]:
                terms.append('"%s"' % parts[i])
    return terms


def make_query(phrase):
    phrase = phrase.strip()
    if isinstance(phrase, str):
        phrase = phrase.decode('utf8')
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ISolrSettings)
    if is_simple_search(phrase):
        terms = split_simple_search(phrase)[:10]
        pattern = settings.simple_search_term_pattern
        term_queries = [pattern.format(term=escape(t)) for t in terms]
        if len(term_queries) > 1:
            term_queries = [u'(%s)' % q for q in term_queries]
        query = u' AND '.join(term_queries)
        if len(terms) > 1 or not phrase.isalnum():
            query = u'(%s) OR (%s)' % (
                settings.simple_search_phrase_pattern.format(
                    phrase=escape(phrase)),
                query,
            )
    else:
        pattern = settings.complex_search_pattern
        query = pattern.format(phrase=phrase)
    if settings.local_query_parameters:
        query = settings.local_query_parameters + query
    return query


def make_path_filter(path, depth=0, include_self=False):
    filters = []
    if depth == 0:
        filters.append(u'path:{}'.format(ensure_text(escape(path))))
    else:
        filters.append(u'path_parent:{}'.format(ensure_text(escape(path))))
    if depth > 0:
        current_depth = len(path.split('/')) - 1
        min_depth = current_depth if include_self else current_depth + 1
        max_depth = current_depth + depth
        if max_depth == min_depth:
            filters.append(u'path_depth:{}'.format(max_depth))
        else:
            filters.append(u'path_depth:[{} TO {}]'.format(
                min_depth, max_depth))
    return filters


def make_filters(**kwargs):
    manager = getUtility(ISolrConnectionManager)
    filters = []
    for key, value in kwargs.items():
        if key not in manager.schema.fields:
            logger.warning(
                'Ignoring filter criteria for unknown field %s', key)
            continue
        elif key == 'path':
            if isinstance(value, dict):
                filters.extend(make_path_filter(
                    value.get('query'), depth=value.get('depth', 0)))
            else:
                filters.extend(make_path_filter(value))
        elif isinstance(value, (list, tuple)):
            filters.append(u'{}:({})'.format(
                key, escape(u' OR '.join(ensure_text(value)))))
        elif isinstance(value, bool):
            filters.append(u'{}:{}'.format(key, u'true' if value else u'false'))
        elif isinstance(value, (dict, record)):
            query = value.get('query')
            operator = value.get('operator')
            range_ = value.get('range', None)
            if query and isinstance(query, (list, tuple)) and operator:
                operator = u' {} '.format(operator.upper())
                filters.append(u'{}:({})'.format(
                    key, escape(operator.join(ensure_text(query)))))
            elif query and range_ in ['min', 'max', 'minmax']:
                if not isinstance(query, (list, tuple)):
                    query = [query]
                if range_ == 'min':
                    filters.append(u'{}:[{} TO *]'.format(
                        key, escape(to_iso8601(query[0]))))
                elif range_ == 'max':
                    filters.append(u'{}:[* TO {}]'.format(
                        key, escape(to_iso8601(query[0]))))
                elif range_ == 'minmax' and len(query) > 1:
                    filters.append(u'{}:[{} TO {}]'.format(
                        key,
                        escape(to_iso8601(min(query))),
                        escape(to_iso8601(max(query))),
                    ))
        else:
            filters.append(u'{}:{}'.format(key, escape(ensure_text(value))))
    return filters


def ensure_text(value):
    if isinstance(value, bytes):
        value = value.decode('utf8')
    elif isinstance(value, (int, float)):
        value = unicode(value)
    elif isinstance(value, (list, tuple)):
        value = [ensure_text(v) for v in value]
    return value
