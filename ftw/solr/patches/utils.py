# Modified implementation from c.solr.utils:
# - simple terms may contain digits
# - simple terms may contain dots

from re import compile, UNICODE

simpleTerm = compile(r'^[\w\d\.]+$', UNICODE)
def isSimpleTerm(term):
    if isinstance(term, str):
        term = unicode(term, 'utf-8', 'ignore')
    return bool(simpleTerm.match(term.strip()))


operators = compile(r'(.*)\s+(AND|OR|NOT)\s+', UNICODE)
simpleCharacters = compile(r'^[\w\d\?\*\s\.]+$', UNICODE)
def isSimpleSearch(term):
    term = term.strip()
    if isinstance(term, str):
        term = unicode(term, 'utf-8', 'ignore')
    if not term:
        return False

    num_quotes = term.count('"')
    if num_quotes > 0:
        # We consider all queries containing quotes non-simple, whether
        # quotes are balanced or not
        return False

    if bool(operators.match(term)):
        return False
    if bool(simpleCharacters.match(term)):
        return True
    term = term.strip()
    if not term:
        return True
    return False
