from ckan.authz import is_authorized
import ckan.plugins.toolkit as tk


def spc_dcat_show(context, data_dict):
    return is_authorized('package_show', context, data_dict)


@tk.auth_allow_anonymous_access
def spc_thematic_area_list(context, data_dict=None):
    return is_authorized('site_read', context, data_dict)
