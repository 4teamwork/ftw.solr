from AccessControl.SecurityManagement import newSecurityManager
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import queryMultiAdapter
from zope.component.hooks import setSite
from zope.globalrequest import setRequest

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

    # Late import because AccessControl.SpecialUsers may not have been
    # initalized yet if imported too early.
    from AccessControl.SpecialUsers import system as system_user
    user = system_user.__of__(app.acl_users)
    newSecurityManager(app, user)

    setSite(portal)
    return portal


def get_plone_sites(root):
    result = []
    for obj in root.values():
        if obj.meta_type == 'Folder':
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
    parser.add_argument('--max-diff', dest='max_diff', default=5, type=int,
                        help="Maximum items to log in diff. Use negative "
                             "number for infinite.")
    parser.add_argument('--include-allowed-roles-and-users',
                        dest='include_allowed_roles_and_users',
                        default=False,
                        type=bool,
                        help="Include allowedRolesAndUsers index when checking"
                             "whether a document is up to date in solr.")

    # If run with plone.recipe.zope2instance we need to strip the first 2 args
    if sys.argv[0] != 'solr':
        args = args[2:]
    options = parser.parse_args(args)

    # Delay import of the Testing module
    # Importing it before the database is opened, will result in opening a
    # DemoStorage database instead of the one from the config file.
    from Testing.makerequest import makerequest
    app = makerequest(app)
    setRequest(app.REQUEST)
    site = setup_site(app, options)

    max_diff = options.max_diff
    if max_diff < 0:
        max_diff = None

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
            commit_interval=options.commit_interval, idxs=options.indexes,
            max_diff=max_diff,
            include_allowed_roles_and_users=options.include_allowed_roles_and_users)
    elif options.command == 'optimize':
        solr_maintenance.optimize()
        print("Solr index optimized.")
    elif options.command == 'clear':
        solr_maintenance.clear()
        print("Solr index cleared.")
    elif options.command == 'diff':
        solr_maintenance.diff(
            max_diff=max_diff,
            include_allowed_roles_and_users=options.include_allowed_roles_and_users)
    else:
        sys.exit("Unknown command '%s'." % options.command)
