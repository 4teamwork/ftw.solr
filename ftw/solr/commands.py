from AccessControl.SecurityManagement import newSecurityManager
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Testing.makerequest import makerequest
from zope.component import queryMultiAdapter
from zope.component.hooks import setSite
import argparse
import sys


def setup_site(app, options):
    # If no plone site was provided by the command line, try to find one.
    if options.site is None:
        sites = get_plone_sites(app)
        if len(sites) == 1:
            portal = sites[0]
        elif len(sites) > 1:
            sys.exit("Multiple Plone sites found. Please specify which Plone "
                     "site should be used.")
        else:
            sys.exit("No Plone site found.")
    else:
        portal = app.unrestrictedTraverse(options.site, None)
    if not portal:
        sys.exit("Plone site not found at %s" % options.plone_site)

    user = portal.getOwner()
    newSecurityManager(app, user)

    setSite(portal)
    return portal


def get_plone_sites(root):
    result = []
    for obj in root.values():
        if obj.meta_type is 'Folder':
            result = result + get_plone_sites(obj)
        elif IPloneSiteRoot.providedBy(obj):
            result.append(obj)
        elif obj.getId() in getattr(root, '_mount_points', {}):
            result.extend(get_plone_sites(obj))
    return result


def solr(app, args):
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help='Command to perform',
                        choices=['reindex', 'reindex-cataloged', 'sync',
                                 'optimize', 'clear', 'diff'])
    parser.add_argument('-s', dest='site', default=None,
                        help='Absolute path to the Plone site')
    parser.add_argument('--commit-interval', dest='commit_interval',
                        default=100, type=int,
                        help='Interval for intermediate commits')
    parser.add_argument('-i', '--indexes', nargs='*',
                        help='Perform command on the given indexes')
    options = parser.parse_args(args[2:])
    app = makerequest(app)
    site = setup_site(app, options)

    solr_maintenance = queryMultiAdapter(
        (site, site.REQUEST), name=u'solr-maintenance')
    if options.command == 'reindex':
        solr_maintenance.reindex(
            commit_interval=options.commit_interval, idxs=options.indexes)
    elif options.command == 'reindex-cataloged':
        solr_maintenance.reindex_cataloged(
            commit_interval=options.commit_interval, idxs=options.indexes)
    elif options.command == 'sync':
        solr_maintenance.sync(
            commit_interval=options.commit_interval, idxs=options.indexes)
    elif options.command == 'optimize':
        solr_maintenance.optimize()
        print("Solr index optimized.")
    elif options.command == 'clear':
        solr_maintenance.clear()
        print("Solr index cleared.")
    elif options.command == 'diff':
        solr_maintenance.diff()
    else:
        sys.exit("Unknown command '%s'." % options.command)
