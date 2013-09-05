from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite


class Catalog(object):

    @property
    def catalog(self):
        return getToolByName(getSite(), 'portal_catalog')

    def get_indexed_value_for(self, obj, index_name):
        rid = self.catalog.getrid('/'.join(obj.getPhysicalPath()))
        indexed_data = self.catalog._catalog.getIndexDataForRID(rid)
        return indexed_data.get(index_name)

    def get_allowed_roles_and_users(self, obj):
        return self.get_indexed_value_for(obj, 'allowedRolesAndUsers')
