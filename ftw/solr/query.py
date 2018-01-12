from ftw.solr.interfaces import ISolrSettings
from zope.component import getUtility
from plone.registry.interfaces import IRegistry

import re


SPECIAL_CHARS = [
    '+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~',
    '*', '?', ':', '/']

OPERATORS = re.compile(r'(.*)\s+(AND|OR|NOT)\s+', re.UNICODE)


def escape(term):
    for char in SPECIAL_CHARS:
        term = term.replace(char, '\\' + char)
    return term


def is_simple_search(term):
    num_quotes = term.count('"')
    if num_quotes % 2 == 0:
        # Replace quoted parts with a marker
        # "foo bar" -> quoted
        parts = term.split('"')
        new_parts = []
        for i in range(0, len(parts)):
            if i % 2 == 0:
                new_parts.append(parts[i])
            else:
                new_parts.append('quoted')
        term = u''.join(new_parts)
    if bool(OPERATORS.match(term)):
        return False
    if len(term.split()) > 3:
        return False
    return True


def split_simple_search(term):
    parts = term.split('"')
    tokens = []
    for i in range(0, len(parts)):
        if i % 2 == 0:
            # unquoted text
            words = [word for word in parts[i].split() if word]
            tokens.extend(words)
        else:
            # The uneven parts are those inside quotes.
            if parts[i]:
                tokens.append('"%s"' % parts[i])
    return tokens


def make_query(term):
    term = term.strip()
    if isinstance(term, str):
        term = term.decode('utf8')
    term = escape(term)
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ISolrSettings)
    if is_simple_search(term):
        words = split_simple_search(term)
        pattern = settings.simple_search_pattern
        queries = [pattern.format(term=w) for w in words]
        if len(queries) > 1:
            queries = [u'(%s)' % q for q in queries]
        query = u' OR '.join(queries)
    else:
        pattern = settings.complex_search_pattern
        query = pattern.format(term=term)
    if settings.local_query_parameters:
        query = settings.local_query_parameters + query
    return query
