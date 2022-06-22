class SolrConfig(object):

    def __init__(self, manager):
        self.manager = manager
        self.retrieve()

    def retrieve(self):
        """Retrieve the Solr config"""
        conn = self.manager.connection
        if conn is None:
            self.config = {}
        else:
            resp = conn.get('/config')
            self.config = resp.get(u'config', {})

        # Determine language specific fields
        self.langid_fields = []
        self.langid_langs = []
        self.langid_langfields = []
        for chain in self.config.get(u'updateRequestProcessorChain', []):
            if chain.get(u'name', u'') == u'langid':
                processors = chain.get(u'', [])
                for proc in processors:
                    if 'langid.fl' in proc:
                        self.langid_fields = proc[u'langid.fl'].split(u',')
                        self.langid_langs = proc.get(
                            u'langid.whitelist', u'').split(u',')
                        fallback = proc.get(u'langid.fallback')
                        if fallback not in self.langid_langs:
                            self.langid_langs.append(fallback)
                        self.langid_langfields = [
                            u'{}_{}'.format(field, lang)
                            for field in self.langid_fields
                            for lang in self.langid_langs
                        ]
