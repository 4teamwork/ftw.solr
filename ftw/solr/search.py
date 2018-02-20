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

    def search(self, request_handler=u'/select', query=u'*:*', filters=None,
               start=0, rows=1000, sort=None, **params):
        conn = self.manager.connection
        params = {u'params': params}
        params[u'query'] = query
        params[u'offset'] = start
        params[u'limit'] = rows
        if sort is not None:
            params[u'sort'] = sort
        if filters is None:
            filters = []
        if not isinstance(filters, list):
            filters = [filters]
        filters.insert(0, self.security_filter())
        params[u'filter'] = filters
        return conn.search(params, request_handler=request_handler)

    def security_filter(self):
        user = getSecurityManager().getUser()
        roles = user.getRoles()
        if 'Anonymous' in roles:
            return u'allowedRolesAndUsers:Anonymous'
        roles = list(roles)
        roles.append('Anonymous')
        if base_hasattr(user, 'getGroups'):
            groups = [u'user:%s' % x for x in user.getGroups()]
            if groups:
                roles = roles + groups
        roles.append(u'user:%s' % user.getId())
        # Roles with spaces need to be quoted
        roles = [u'"%s"' % escape(r) if ' ' in r else escape(r) for r in roles]
        return u'allowedRolesAndUsers:(%s)' % u' OR '.join(roles)
