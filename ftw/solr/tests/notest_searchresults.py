from zope.interface import implements
from collective.solr.interfaces import ISearch
from collective.solr.parser import SolrResponse
from collective.solr.dispatcher import solrSearchResults

class TestSearchResults(TestCase):

    class DummySearch(object):
        """ a search utility for solr """
        implements(ISearch)

        def __init__(self):
            self.mngr = SolrConnectionManager()
            self.mngr.setHost(active=True)
            conn = self.mngr.getConnection()
            fakehttp(conn, getData('plone_schema.xml')) # fake schema response
            self.mngr.getSchema()                       # read and cache the schema
        def getManager(self):
            return self.mngr

        def search(self, query, **parameters):
            results = SolrResponse(getData('facet_xml_response.txt'))
            results.query = query
            results.parameters = parameters
            return results

        __call__ = search
        buildQuery = buildQuery


    def setUp(self):
        
        provideUtility(SolrConnectionConfig(), ISolrConnectionConfig)
        provideUtility(TestSearchResults.DummySearch(), ISearch)
        # self.mngr = SolrConnectionManager()
        # self.mngr.setHost(active=True)
        # conn = self.mngr.getConnection()
        # fakehttp(conn, getData('plone_schema.xml')) # fake schema response
        # self.mngr.getSchema()                       # read and cache the schema
        # self.search = Search()
        # self.search.manager = self.mngr

        # Patch buildQuery method
        # self.search.buildQuery = buildQuery.__get__(self.search,
        #                                             self.search.__class__)

    def test_foo(self):
        pass
        #import pdb; pdb.set_trace( )

