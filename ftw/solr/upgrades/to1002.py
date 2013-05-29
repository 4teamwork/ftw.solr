from ftw.upgrade import UpgradeStep


class Upgrades(UpgradeStep):

    def __call__(self):
        self.setup_install_profile(
            'profile-ftw.solr.upgrades:1002')
