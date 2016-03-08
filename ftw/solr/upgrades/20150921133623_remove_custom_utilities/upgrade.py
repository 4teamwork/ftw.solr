from ftw.upgrade import UpgradeStep


class RemoveCustomUtilities(UpgradeStep):
    """Remove custom utilities.
    """

    def __call__(self):
        self.install_upgrade_profile()
