Introduction
============

`ftw.solr` provides various customizations and enhancements on top of 
`collective.solr` which integrates the Solr search engine with Plone.


Features
========

Highlighting (aka Snippets)
---------------------------

When displaying search results, Plone by default displays the title and the 
description of an item. Solr, like Google and other search engines, can return a 
snippet of the text containing the words searched for. `ftw.solr` enables this
feature in Plone.

Live search grouping
--------------------

Search results in Plone's live search can be grouped by portal_type. This is 
the way search results are shown in Spotlight on Mac OS X.

Facet queries
-------------

In addition to facet fields support provided by `collective.solr`, 
`ftw.solr` adds support for facet queries. This type of faceting offers a lot 
of flexibility. Instead of choosing a specific field to facet its values, multiple 
Solr queries can be specified, that themselve become facets.

Ajax-ified search form
----------------------

The search form is fully ajax-ified which leads to faster search results when
changing search criteria.


Solr Configuration
==================

Search Handlers
---------------

`ftw.solr` requires two custom search handlers that must be configured on the Solr server.

The ``livesearch`` request handler is used for live search and should limit the 
returned fields to a minimum for maximum speed. Example::

    <requestHandler name="livesearch" class="solr.SearchHandler">
        <lst name="defaults">
            <str name="echoParams">explicit</str>
            <int name="rows">1000</int>
        </lst>
        <lst name="invariants">
            <str name="fl">Title Description portal_type path_string getIcon</str>
        </lst>
    </requestHandler>

The ``hlsearch`` request handler should contain the configuration for higlighting. Example::

    <requestHandler name="hlsearch" class="solr.SearchHandler">
        <lst name="defaults">
            <str name="echoParams">explicit</str>
            <int name="rows">10</int>
            <bool name="hl">true</bool>
            <bool name="hl.useFastVectorHighlighter">true</bool>
            <str name="hl.fl">snippetText</str>
            <int name="hl.fragsize">200</int>
            <str name="hl.alternateField">Description</str>
            <int name="hl.maxAlternateFieldLength">200</int>
            <int name="hl.snippets">3</int>
        </lst>
    </requestHandler>

Field types and indexes
-----------------------

Highlighting requires an index named ``snippetText`` with it's own field type which does not too much text analysis.
Example::

    <fieldType name="text_snippets" class="solr.TextField" positionIncrementGap="100">
      <analyzer type="index">
          <tokenizer class="solr.WhitespaceTokenizerFactory"/>
          <filter class="solr.LowerCaseFilterFactory"/>
      </analyzer>
      <analyzer type="query">
          <tokenizer class="solr.WhitespaceTokenizerFactory"/>
          <filter class="solr.LowerCaseFilterFactory"/>
      </analyzer>
    </fieldType>
 
    <field name="snippetText" type="text_snippets" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="true" termPositions="true"
           termOffsets="true"/>


Installation
============

Install `ftw.solr` by adding it to the list of eggs in your 
buildout or by adding it as a dependency of your policy package. Then run 
buildout and restart your instance.

Go to Site Setup of your Plone site and activate the `ftw.solr` add-on. Check 
the Solr control panel provided by `collective.solr` for Solr-specific 
configuration options.


Copyright
=========

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

`ftw.solr` is licensed under GNU General Public License, version 2.
