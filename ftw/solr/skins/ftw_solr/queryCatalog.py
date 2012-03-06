## Script (Python) "queryCatalog"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=REQUEST=None,show_all=0,quote_logic=0,quote_logic_indexes=['SearchableText','Description','Title'],use_types_blacklist=False,show_inactive=False,use_navigation_root=False,b_start=None,b_size=None
##title=wraps the portal_catalog with a rules qualified query
##
qc_view = context.restrictedTraverse('@@querycatalog')
return qc_view.querycatalog(REQUEST, show_all, quote_logic,
                            quote_logic_indexes, use_types_blacklist,
                            show_inactive, use_navigation_root, b_start,
                            b_size)
