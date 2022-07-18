from ftw.upgrade import UpgradeStep


class AddEnableUpdatesInPostCommitHookSetting(UpgradeStep):
    """Add registry setting for enabling/disabling updates in post commit hook.
    """

    def __call__(self):
        self.install_upgrade_profile()
