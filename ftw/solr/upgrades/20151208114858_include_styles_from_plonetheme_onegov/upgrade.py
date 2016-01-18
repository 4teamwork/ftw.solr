from ftw.upgrade import UpgradeStep


class IncludeStylesFromPlonethemeOnegov(UpgradeStep):
    """Include styles from plonetheme onegov.
    """

    def __call__(self):
        self.install_upgrade_profile()
