from ftw.upgrade import UpgradeStep


class RegisterLocalUtilities(UpgradeStep):

    def __call__(self):
        self.setup_install_profile(
            'profile-ftw.solr.upgrades:1004')