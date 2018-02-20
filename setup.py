# -*- coding: utf-8 -*-
"""Installer for the ftw.solr package."""

from setuptools import find_packages
from setuptools import setup
import os


long_description = '\n\n'.join([
    open('README.rst').read(),
    open(os.path.join("docs", "HISTORY.txt")).read(),
])

tests_require = [
    'plone.app.testing',
    'plone.app.dexterity',
    'plone.testing',
    'plone.api',
    'pytz',
    'mock',
]

setup(
    name='ftw.solr',
    version='2.1.1',
    description="Solr integration for Plone",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='Plone Solr',
    author='Thomas Buchberger',
    author_email='t.buchberger@4teamwork.ch',
    url='https://pypi.python.org/pypi/ftw.solr',
    license='GPL version 2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['ftw'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
        'setuptools',
        'collective.indexing',
        'plone.app.contentlisting',
        'plone.app.layout',
        'plone.namedfile[blobs]',
    ],
    extras_require=dict(test=tests_require, tests=tests_require),
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
