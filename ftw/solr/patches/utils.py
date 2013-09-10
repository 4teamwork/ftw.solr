# Modified implementation from c.solr.utils:
# Treat search terms ending with a digit as simple

from re import compile, UNICODE


simpleTerm = compile(r'^[\w\d]+$', UNICODE)
def isSimpleTerm(term):
    if isinstance(term, str):
        term = unicode(term, 'utf-8', 'ignore')
    return bool(simpleTerm.match(term.strip()))


operators = compile(r'(.*)\s+(AND|OR|NOT)\s+', UNICODE)
simpleCharacters = compile(r'^[\w\d\?\*\s]+$', UNICODE)
def isSimpleSearch(term):
    term = term.strip()
    if isinstance(term, str):
        term = unicode(term, 'utf-8', 'ignore')
    if not term:
        return False
    num_quotes = term.count('"')
    if num_quotes % 2 == 1:
        return False
    if num_quotes > 1:
        # replace the quoted parts of the query with a marker
        parts = term.split('"')
        # take only the even parts (i.e. those outside the quotes)
        new_parts = []
        for i in range(0, len(parts)):
            if i % 2 == 0:
                new_parts.append(parts[i])
            else:
                new_parts.append('quoted')
        term = u''.join(new_parts)
    if bool(operators.match(term)):
        return False
    if bool(simpleCharacters.match(term)):
        return True
    term = term.strip()
    if not term:
        return True
    return False
