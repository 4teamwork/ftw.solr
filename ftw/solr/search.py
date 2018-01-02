from AccessControl.SecurityManagement import getSecurityManager
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrSearch
from Products.CMFPlone.utils import base_hasattr
from zope.component import queryUtility
from zope.interface import implementer


SPECIAL_CHARS = [
    '+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~',
    '*', '?', ':', '/']


def escape(string):
    for char in SPECIAL_CHARS:
        string = string.replace(char, '\\' + char)
    return string


def allowed_roles_and_users(user):
    result = user.getRoles()
    if 'Anonymous' in result:
        # The anonymous user has no further roles
        return ['Anonymous']
    result = list(result)
    if base_hasattr(user, 'getGroups'):
        groups = ['user:%s' % x for x in user.getGroups()]
        if groups:
            result = result + groups
    # Order the arguments from small to large sets
    result.insert(0, 'user:%s' % user.getId())
    result.append('Anonymous')
    return result


@implementer(ISolrSearch)
class SolrSearch(object):
    """A search utility for Solr """

    def __init__(self):
        self._manager = None

    @property
    def manager(self):
        if self._manager is None:
            self._manager = queryUtility(ISolrConnectionManager)
        return self._manager

    def search(self, request_handler='/select', query='*:*', filter=None,
               start=0, rows=1000, **params):
        conn = self.manager.connection
        params = {'params': params}
        params['query'] = query
        params['offset'] = start
        params['limit'] = rows
        user = getSecurityManager().getUser()
        params['filter'] = 'allowedRolesAndUsers:(%s)' % escape(' OR '.join(
            allowed_roles_and_users(user)))
        return conn.search(params, request_handler=request_handler)

    def security_filter(self):
        user = getSecurityManager().getUser()
        roles = user.getRoles()
        if 'Anonymous' in roles:
            return ['Anonymous']
        roles = list(roles)
        if base_hasattr(user, 'getGroups'):
            groups = ['user:%s' % x for x in user.getGroups()]
            if groups:
                roles = roles + groups
        roles.insert(0, 'user:%s' % user.getId())
        roles.append('Anonymous')
        return 'allowedRolesAndUsers:(%s)' % escape(' OR '.join(roles))
