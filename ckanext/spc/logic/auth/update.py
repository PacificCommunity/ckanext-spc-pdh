from ckan.logic.auth.update import resource_update
from ckan.authz import is_sysadmin

from ckanext.spc.utils import is_resource_updatable


def spc_resource_update(context, data_dict):
    if not is_resource_updatable(data_dict['id']):
        return {'success': False}
    return resource_update(context, data_dict)


def spc_import_datasets(context, data_dict):
    is_sys = is_sysadmin(context['user'])
    return {'success': is_sys}
