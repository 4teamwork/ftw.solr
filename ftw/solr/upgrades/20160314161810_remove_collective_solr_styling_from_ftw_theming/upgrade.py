from ftw.upgrade import UpgradeStep


class RemoveCollectiveSolrStylingFromFtwTheming(UpgradeStep):
    """Remove collective solr styling from ftw.theming.
    """

    def __call__(self):
        self.install_upgrade_profile()
