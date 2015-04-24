from setuptools import setup, find_packages
import os

version = '1.4.2'

tests_require = [
    'ftw.builder',
    'plone.app.dexterity',
    'plone.app.testing',
    ]

setup(name='ftw.solr',
      version=version,
      description="Solr integration for Plone using collective.solr",
      long_description=open("README.rst").read() + "\n" + \
          open(os.path.join("docs", "HISTORY.txt")).read(),

      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],

      keywords='ftw solr',
      author='4teamwork GmbH',
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.solr',
      license='GPL2',

      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
        'setuptools',
        'collective.solr',
        'ftw.upgrade',
        'collective.monkeypatcher',
        'plone.app.contentlisting',
        'plone.app.search',
        'requests',
        ],

      tests_require=tests_require,
      extras_require=dict(tests=tests_require),

      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
