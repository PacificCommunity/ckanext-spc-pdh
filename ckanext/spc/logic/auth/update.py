from ckan.logic.auth.update import resource_update

from ckanext.spc.utils import is_resource_updatable


def spc_resource_update(context, data_dict):
    if not is_resource_updatable(data_dict['id']):
        return {'success': False}
    return resource_update(context, data_dict)
