import ckan.model as model
from ckan.logic.auth.delete import resource_delete


def spc_resource_delete(context, data_dict):
    res = model.Resource.get(data_dict['id'])

    if not res.package.private:
        return {'success': False}
    return resource_delete(context, data_dict)
