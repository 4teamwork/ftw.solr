from ftw.builder import builder_registry
from ftw.builder.dexterity import DexterityBuilder


class DexterityFolderBuilder(DexterityBuilder):
    portal_type = 'DexterityFolder'


builder_registry.register('dexterity folder', DexterityFolderBuilder)
