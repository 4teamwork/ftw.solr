from ftw.solr.interfaces import ISolrSettings
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import re


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
