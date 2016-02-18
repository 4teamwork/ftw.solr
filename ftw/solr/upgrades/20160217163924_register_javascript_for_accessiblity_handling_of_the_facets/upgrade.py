from ftw.upgrade import UpgradeStep


class RegisterJavascriptForAccessiblityHandlingOfTheFacets(UpgradeStep):
    """Register javascript for accessiblity handling of the facets.
    """

    def __call__(self):
        self.install_upgrade_profile()
