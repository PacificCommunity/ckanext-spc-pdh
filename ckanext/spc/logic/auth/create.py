from ckan.logic.auth.create import resource_create
from ckanext.spc.utils import is_resource_updatable


def spc_resource_create(context, data_dict):
    id = data_dict.get('id', data_dict.get('package_id'))
    package_id = True if 'package_id' in data_dict else False

    if not is_resource_updatable(id, package_id):
        return {'success': False}

    return resource_create(context, data_dict)
