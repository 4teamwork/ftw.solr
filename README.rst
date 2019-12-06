Introduction
============

``ftw.solr`` integrates the Solr search engine with Plone.

.. IMPORTANT::
   Since version 2.0 ftw.solr no longer depends on collective.solr. Instead it
   provides it's own Solr integration using Solr's REST API. Version 2.0 is a
   complete rewrite and is not compatible with ftw.solr 1.x.

ftw.solr does not try to replace the portal catalog of Plone and does not hook
into the catalog's search function. Instead it provides a search utiltity that
must be used explicitly. It's meant to be used in search forms for fulltext
searches while the portal catalog is still in use for things like navigation
or folder contents. The goal is to get rid off all fulltext indexes
(e.g. ZCTextIndex) in the portal catalog.

ftw.solr requires Apache Solr 7.0 or higher.


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


Solr installation
-----------------

To install a Solr server with buildout you can use the ``ftw.recipe.solr`` recipe.

.. code::

    [solr]
    recipe = ftw.recipe.solr
    cores = mycore


Configure the Solr connection
-----------------------------

The connections settings for Solr can be configured in ZCML and thus in
buildout. Example::

    [instance]
    zcml-additional =
        <configure xmlns:solr="http://namespaces.plone.org/solr">
            <solr:connection host="localhost" port="8983" base="/solr/mycore"/>
       </configure>

By default, ``ftw.solr`` will do full text extraction by passing the blob's
filesystem path to the Solr Cell extract handler, assuming that Solr runs on
the same machine and has access to the blob storage.

For setups where this isn't desired, the connection option ``upload_blobs``
can be set to ``true`` in order to make ``ftw.solr`` upload the blobs directly
to the extract handler via HTTP POST::

    [instance]
    zcml-additional =
        <configure xmlns:solr="http://namespaces.plone.org/solr">
            <solr:connection host="localhost" port="8983" base="/solr/mycore" upload_blobs="true"/>
       </configure>


Run buildout
------------

After running buildout and restarting your instance you can install the ftw.solr
addon in Plone.


Usage
=====

Get the ``ISolrSearch`` utility and call the search method to get search results
from Solr.

.. code:: python

    from ftw.solr.interfaces import ISolrSearch
    from zope.component import getUtility

    solr = getUtility(ISolrSearch)
    resp = solr.search(query=u'SearchableText:foo')


You can get a ``plone.app.contentlisting`` style result by adapting ``IContentListing``:

.. code:: python

    from plone.app.contentlisting.interfaces import IContentListing
    listing = IContentListing(resp)


Solr Index Maintenance
======================

For indexing Plone content and other maintenance work you can use the ``solr`` Zope command.
Run ``bin/instance solr -h`` for available options.

Clear the Solr index:

.. code::

    bin/instance solr clear

Rebuild the complete Solr index:

.. code::

    bin/instance solr reindex

Reindex specific indexes:

.. code::

    bin/instance solr reindex -i modified created

Synchronize the Solr index with the portal catalog:

.. code::

    bin/instance solr sync


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
