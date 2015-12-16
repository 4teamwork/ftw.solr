from ftw.upgrade import UpgradeStep


class AddDefaultSolrInstallation(UpgradeStep):
    """Add default solr installation.
    """

    def __call__(self):
        self.install_upgrade_profile()
