Configuration
=============



solrconfig.xml
--------------

Use ``solrconfig.xml`` from examples\default

Remove or comment out unused contrib modules:
- solr-clustering
- solr-langid
- solr-velocity


Enable remote streaming::

  <requestParsers enableRemoteStreaming="true"
                  multipartUploadLimitInKB="-1"
                  formdataUploadLimitInKB="-1"
                  addHttpRequestToContext="false"/>


Configure /update/extract request handler defaults::

  <requestHandler name="/update/extract"
                  startup="lazy"
                  class="solr.extraction.ExtractingRequestHandler" >
    <lst name="defaults">
      <str name="lowernames">false</str>
      <str name="xpath">/xhtml:html/xhtml:body//text()</str>
      <str name="fmap.content">SearchableText</str>
      <str name="uprefix">ignored_</str>
    </lst>
  </requestHandler>


Configure analyzer field type and field name for spellchecker::

  <searchComponent name="spellcheck" class="solr.SpellCheckComponent">

    <str name="queryAnalyzerFieldType">text</str>

    <!-- Multiple "Spell Checkers" can be declared and used by this
         component
      -->

    <!-- a spellchecker built from a field of the main index -->
    <lst name="spellchecker">
      <str name="name">default</str>
      <str name="field">SearchableText</str>
      ...

Enable spellcheck component in /select search handler::

    <arr name="last-components">
      <str>spellcheck</str>
    </arr>

Remove or comment out update processors part.




docker run -dt -p 8983:8983 -v $(pwd)/solr-instancedir:/opt/solr/server/solr/ftwsolr solr:7.2
