from ckan.logic.auth.delete import resource_delete
from ckanext.spc.utils import is_resource_updatable


def spc_resource_delete(context, data_dict):
    if not is_resource_updatable(data_dict['id']):
        return {'success': False}
    return resource_delete(context, data_dict)
