from ckan.logic.auth.create import resource_create

from ckanext.spc.utils import is_resource_updatable


def spc_resource_create(context, data_dict):
    if not is_resource_updatable(None, data_dict['package_id']):
        return {'success': False}
    return resource_create(context, data_dict)
