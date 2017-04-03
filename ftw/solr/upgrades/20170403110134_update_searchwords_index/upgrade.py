from ftw.solr.behaviors import ISearchwords
from ftw.upgrade import UpgradeStep
from plone.dexterity.interfaces import IDexterityContent


class UpdateSearchwordsIndex(UpgradeStep):
    """Update searchwords index.
    """

    def __call__(self):
        query = {'object_provides': {
            'query': [ISearchwords.__identifier__,
                      IDexterityContent.__identifier__],
            'operator': 'and'}}
        for obj in self.objects(query, 'Update searchwords index'):
            if ISearchwords(obj).searchwords:
                obj.reindexObject(idxs=['searchwords'])
        self.install_upgrade_profile()
