from AccessControl.SecurityManagement import getSecurityManager
from ftw.solr.interfaces import ISolrConnectionManager
from ftw.solr.interfaces import ISolrSearch
from ftw.solr.query import escape
from Products.CMFPlone.utils import base_hasattr
from zope.component import queryUtility
from zope.interface import implementer


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
        if filter is None:
            filter = []
        if not isinstance(filter, list):
            filter = [filter]
        params['filter'] = filter
        params['filter'].insert(0, self.security_filter())
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
