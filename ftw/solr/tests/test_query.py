from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.manager import SolrConnectionConfig
from collective.solr.manager import SolrConnectionManager
from collective.solr.search import Search
from collective.solr.tests.utils import getData, fakehttp
from ftw.solr.patches.search import buildQueryAndParameters
from unittest import TestCase
from zope.component import provideUtility


class TestBuildQuery(TestCase):

    def setUp(self):
        provideUtility(SolrConnectionConfig(), ISolrConnectionConfig)
        self.mngr = SolrConnectionManager()
        self.mngr.setHost(active=True)
        conn = self.mngr.getConnection()
        fakehttp(conn, getData('plone_schema.xml'))  # fake schema response
        self.mngr.getSchema()                       # read and cache the schema
        self.search = Search()
        self.search.manager = self.mngr

        # Patch buildQuery method
        self.search.buildQuery = buildQueryAndParameters.__get__(
            self.search,
            self.search.__class__)

    def tearDown(self):
        self.mngr.closeConnection()
        self.mngr.setHost(active=False)

    def build_query(self, *args, **kwargs):
        query = self.search.buildQuery(*args, **kwargs)[0]
        return ' '.join(sorted(query.values()))

    def test_simple_path_query(self):
        self.assertEquals('+path_parents:\\/spam\\/and\\/eggs',
                          self.build_query(path_parents='/spam/and/eggs'))

    def test_path_list_query(self):
        self.assertEquals('+path_parents:("\\/spam" OR "\\/eggs")',
                          self.build_query(path_parents=['/spam', '/eggs']))

    def test_slash_in_searchabletext(self):
        self.assertEquals('+SearchableText:spam\\/eggs',
                          self.build_query(SearchableText='spam/eggs'))

    def test_queries_with_path_and_depth_should_be_escaped(self):
        self.assertEquals(
            '+path_depth:[4 TO 6] AND +path_parents:\\/spam\\/and\\/eggs',
            self.build_query(
                path_parents=set(['+path_depth:[4 TO 6] AND '
                                  '+path_parents:/spam/and/eggs'])))
