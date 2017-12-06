from AccessControl.SecurityManagement import getSecurityManager
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrSearch
from Products.CMFPlone.utils import base_hasattr
from zope.component import queryUtility
from zope.interface import implementer


SPECIAL_CHARS = [
    '\\', '+', '-', '&&', '||', '!', '(', ')', '{', '}', '[', ']', '^', '"',
    '~', '*', '?', ':', '/']


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

    def search(self, request_handler='/select', query='*:*', start=0,
               rows=1000, **params):
        conn = self.manager.connection
        params = {'params': params}
        params['query'] = query
        params['offset'] = start
        params['limit'] = rows
        user = getSecurityManager().getUser()
        params['filter'] = 'allowedRolesAndUsers:(%s)' % ' OR '.join(
            allowed_roles_and_users(user))
        return conn.post(path=request_handler, data=params)
