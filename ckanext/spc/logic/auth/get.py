import ckan.plugins.toolkit as tk
from ckan.authz import is_authorized

def spc_dcat_show(context, data_dict):
    return is_authorized('package_show', context, data_dict)
