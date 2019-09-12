from ftw.upgrade import UpgradeStep


class AddEnableSetting(UpgradeStep):
    """Add registry setting for enabling/disabling indexing
    """

    def __call__(self):
        self.install_upgrade_profile()
