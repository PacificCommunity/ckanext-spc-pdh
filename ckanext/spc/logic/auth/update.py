import ckan.authz as authz
from ckan.logic.auth.update import resource_update

from ckanext.spc.utils import is_resource_updatable


def spc_resource_update(context, data_dict):
    if not is_resource_updatable(data_dict['id']):
        return {'success': False}
    return resource_update(context, data_dict)


def spc_import_datasets(context, data_dict):
    return {'success': authz.has_user_permission_for_group_or_org(
        data_dict['id'], context['user'], 'admin'
    )}
