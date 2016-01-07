Introduction
============

``ftw.solr`` provides various customizations and enhancements on top of
``collective.solr`` which integrates the Solr search engine with Plone.

.. contents:: Table of Contents

Features
========

Atomic updates (aka partial updates)
------------------------------------

Since Solr 4.0 it's possible to update fields in a Solr document individually,
sending only the fields that actually changed, whereas before it was necessary
to send *all* the fields again every time something changed (and therefore ask
Plone again to index them all, causing a massive performance penalty).

``ftw.solr`` supports atomic updates for Solr version 4.1 and above.
In order for atomic updates to work, three things must be taken care of:

- An ``<updateLog />`` must be enabled in ``solrconfig.xml``. If it's missing,
  Solr will reject any update messages that contain atomic update instructions.
- A ``_version_`` field must be defined in the Solr schema.
- All fields in the Solr schema must be defined with ``stored="true"``

In the stock Solr configs from 4.1 upwards ``<updateLog />`` and the
``_version_`` field are already configured correctly. If you're using
``collective.recipe.solrinstance``, check the generated ``solrconfig.xml``,
it might not have been updated for the use of atomic updates yet.

If there's a field in the Solr schema that's *not* ``stored="true"``,
it will get
**dropped** from documents in Solr on the next update to that document.
Indexing won't fail, but that field simply won't have any content any more.

Apart from those prerequisites, there's nothing more to be done in order to use
atomic updates. ``ftw.solr`` will automatically perform atomic updates whenever
possible.

Also see http://wiki.apache.org/solr/Atomic_Updates

Highlighting (aka Snippets)
---------------------------

When displaying search results, Plone by default displays the title and the
description of an item. Solr, like Google and other search engines, can return a
snippet of the text containing the words searched for.
``ftw.solr`` enables this feature in Plone.

Live search grouping
--------------------

Search results in Plone's live search can be grouped by ``portal_type``.
This is the way search results are shown in Spotlight on Mac OS X.

Facet queries
-------------

In addition to facet fields support provided by ``collective.solr``,
``ftw.solr`` adds support for facet queries.
This type of faceting offers a lot of flexibility.
Instead of choosing a specific field to facet its values, multiple
Solr queries can be specified, that themselves become facets.

Word Cloud
----------

Assuming there is a correctly configured index ``wordCloudTerms``,
a Word Cloud
showing the most common terms across documents can be displayed.

The Word Cloud is implemented in a browser view that can either be displayed
stand-alone by traversing to ``/@@wordcloud`` or rendered in a portlet.

Ajax-ified search form
----------------------

The search form is fully ajax-ified which leads to faster search results when
changing search criteria.

Solr connection configuration in ZCML
-------------------------------------

The connections settings for Solr can be configured in ZCML and thus in
buildout. This makes it easier when copying databases between multiple Zope
instances with different Solr servers. Example::

    zcml-additional =
        <configure xmlns:solr="http://namespaces.plone.org/solr">
            <solr:connection host="localhost" port="8983" base="/solr"/>
       </configure>


Solr Configuration
==================

Search Handlers
---------------

``ftw.solr`` requires two custom search handlers that must be configured on the
Solr server. Search handlers are configured in ``solrconfig.xml`` of your
collection.

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

The ``hlsearch`` request handler should contain the configuration for highlighting.
Example::

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

Highlighting
~~~~~~~~~~~~

Highlighting requires an index named ``snippetText``
with its own field type which does not do too much text analysis.
Fields and indexes are configured in ``schema.xml`` of your collection.

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

Word Cloud
~~~~~~~~~~

The Word Cloud feature requires an index named ``wordCloudTerms``
with it's own field type.
It's basically a copy of ``SearchableText`` but with less analysis and
filtering (no lowercasing, no character normalization, etc...).

Field type example::

    <fieldType name="cloud_terms" class="solr.TextField" positionIncrementGap="100">
      <analyzer type="index">
          <tokenizer class="solr.WhitespaceTokenizerFactory"/>
          <filter class="solr.StopFilterFactory" ignoreCase="true" words="${buildout:directory}/german_stop.txt" enablePositionIncrements="true"/>
          <filter class="solr.WordDelimiterFilterFactory"
                  splitOnCaseChange="1"
                  splitOnNumerics="1"
                  stemEnglishPossessive="1"
                  generateWordParts="0"
                  generateNumberParts="0"
                  catenateWords="0"
                  catenateNumbers="0"
                  catenateAll="0"
                  preserveOriginal="1"/>
          <!-- Strip punctuation characters from beginning and end of terms -->
          <filter class="solr.PatternReplaceFilterFactory" pattern="^(\p{Punct}*)(.*?)(\p{Punct}*)$" replacement="$2"/>
          <!-- Filter everything that does not contain at least 3 regular letters -->
          <filter class="solr.PatternReplaceFilterFactory" pattern="^([^a-zA-Z]*)([a-zA-Z]{0,2})([^a-zA-Z]*)$" replacement=""/>
          <!-- Filter any term shorter than 3 characters (incl. empty string) -->
          <filter class="solr.LengthFilterFactory" min="2" max="50"/>
      </analyzer>
    </fieldType>

Index example::

    <field name="wordCloudTerms" type="cloud_terms" indexed="true"
           stored="true" required="false" multiValued="false"
           termVectors="true" termPositions="true"
           termOffsets="true"/>

    <copyField source="SearchableText" dest="wordCloudTerms"/>


Search / Livesearch
-------------------

``ftw.solr`` provides a better livesearch implementation using jQuery Autocomplete widget.
A new search and result template is also included.

Suggestions
-----------
By default suggestions are disabled on the advanced search input field.
if you want autocomplete while typing you need to install the autocomplete profile of ftw.solr and...

**Prerequisit (solr config)**::

    <!-- Suggester for autocomplete -->
    <searchComponent class="solr.SpellCheckComponent" name="suggest">
      <lst name="spellchecker">
        <str name="name">suggest</str>
        <str name="classname">org.apache.solr.spelling.suggest.Suggester</str>
        <str name="lookupImpl">org.apache.solr.spelling.suggest.fst.WFSTLookupFactory</str>
        <str name="field">SearchableText</str>
        <float name="threshold">0.0005</float>
      </lst>
    </searchComponent>
    <requestHandler class="org.apache.solr.handler.component.SearchHandler" name="/suggest">
      <lst name="defaults">
        <str name="spellcheck">true</str>
        <str name="spellcheck.dictionary">suggest</str>
        <str name="spellcheck.onlyMorePopular">true</str>
        <str name="spellcheck.count">10</str>
      </lst>
      <arr name="components">
        <str>suggest</str>
      </arr>
    </requestHandler>


The portal searchbox no longer provides this feature in favor of the new livesearch autocomplete feature.



Installation
============

Add as dependency
-----------------

Install ``ftw.solr`` by adding it to the list of eggs in your
buildout or by adding it as a dependency of your policy package.

.. code:: rst

    [instance]
    eggs +=
        ftw.solr

Extend your buildout
--------------------

For production:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/production.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/solr.cfg

    deployment-number = 05

For local development:

.. code:: ini

    [buildout]
    extends =
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development.cfg
        https://raw.githubusercontent.com/4teamwork/ftw-buildouts/master/plone-development-solr.cfg

Update medatata.xml
-------------------

Add ``ftw.solr`` to your metadata.xml:

.. code:: xml

    <?xml version="1.0"?>
    <metadata>
        <dependencies>
            <dependency>profile-ftw.solr:default</dependency>
        </dependencies>
    </metadata>

Run buildout
------------

If you configured your solr, you can buildout and restart your instance.

- Install the generic setup profile of ``ftw.solr``.


Links
=====

- Github: https://github.com/4teamwork/ftw.solr
- Issues: https://github.com/4teamwork/ftw.solr/issues
- Pypi: http://pypi.python.org/pypi/ftw.solr
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.solr


Copyright
=========

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.solr`` is licensed under GNU General Public License, version 2.
