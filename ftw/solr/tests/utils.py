from collective.dexteritytextindexer.behavior import IDexterityTextIndexer
from ftw.solr import tests
from os.path import dirname, join
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import queryUtility


def getData(filename):
    """ return a file object from the test data folder """
    filename = join(dirname(tests.__file__), 'data', filename)
    return open(filename, 'r').read()


def enable_textindexer_behavior(type_):
    fti = queryUtility(IDexterityFTI, name=type_)
    behaviors = list(fti.behaviors)
    behaviors.append(IDexterityTextIndexer.__identifier__)
    fti.behaviors = tuple(behaviors)
