from collective.indexing.queue import getQueue
from ftw.builder import Builder
from ftw.builder import create
from ftw.solr.testing import SOLR_FUNCTIONAL_TESTING
from ftw.solr.tests.pages import Catalog
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from unittest2 import TestCase
import transaction


class TestReindexingSecurity(TestCase):

    layer = SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)

    def get_indexing_queue_length(self):
        return getQueue().length()

    def folder_builder(self):
        return Builder('folder')

    def test_indexes_are_updated_recursively(self):
        folder = create(self.folder_builder())
        subfolder = create(self.folder_builder().within(folder))

        self.assertEquals(
            {'folder': ['Anonymous'],
             'subfolder': ['Anonymous']},

            {'folder': Catalog().get_allowed_roles_and_users(folder),
             'subfolder': Catalog().get_allowed_roles_and_users(subfolder)})

        folder.manage_permission('View', roles=['Manager'], acquire=False)
        folder.reindexObjectSecurity()
        self.assertEquals(2, self.get_indexing_queue_length())
        transaction.commit()

        self.assertEquals(
            {'folder': set(['Manager']),
             'subfolder': set(['Manager'])},

            {'folder': set(Catalog().get_allowed_roles_and_users(folder)),
             'subfolder': set(Catalog().get_allowed_roles_and_users(subfolder))})

    def test_resursive_indexing_is_not_done_when_subobjects_do_not_acquire(self):
        folder = create(self.folder_builder())
        folder.manage_permission('View', roles=['Reader'], acquire=False)
        folder.reindexObjectSecurity()

        subfolder = create(self.folder_builder().within(folder))
        subfolder.manage_permission('View', roles=['Reader'], acquire=False)
        subfolder.reindexObjectSecurity()
        transaction.commit()

        self.assertEquals(
            {'folder': ['Reader'],
             'subfolder': ['Reader']},

            {'folder': Catalog().get_allowed_roles_and_users(folder),
             'subfolder': Catalog().get_allowed_roles_and_users(subfolder)})

        self.assertEquals(0, self.get_indexing_queue_length(),
                          'Queue should be empty at this point.')
        folder.manage_permission('View', roles=['Manager'], acquire=False)
        folder.reindexObjectSecurity()
        self.assertEquals(1, self.get_indexing_queue_length(),
                          'Only the folder should be reindexed at this point,'
                          ' since the subfolder does not acquire the View permission.')
        transaction.commit()

        self.assertEquals(
            {'folder': ['Manager'],
             'subfolder': ['Reader']},

            {'folder': Catalog().get_allowed_roles_and_users(folder),
             'subfolder': Catalog().get_allowed_roles_and_users(subfolder)})


class TestDexterityReindexingSecurity(TestReindexingSecurity):

    def folder_builder(self):
        return Builder('dexterity folder')
