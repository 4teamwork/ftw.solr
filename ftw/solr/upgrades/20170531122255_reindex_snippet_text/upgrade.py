from ftw.upgrade import UpgradeStep
from collective.solr.interfaces import ISearch
from zope.component import getUtility

class ReindexSnippetText(UpgradeStep):
    """Reindex snippet text.
    """

    def __call__(self):
        search = getUtility(ISearch)
        objs = search.search('snippetText: *<*')
        for item in objs.results():
            self.portal.restrictedTraverse(item.path_string +
                                           '/solr-maintenance/reindex')(
                limit=1,
                idxs=['snippetText'])
        self.install_upgrade_profile()