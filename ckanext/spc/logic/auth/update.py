import ckan.model as model
from ckan.logic.auth.update import resource_update


def spc_resource_update(context, data_dict):
    res = model.Resource.get(data_dict['id'])
    if not res.package.private:
        return {'success': False}
    return resource_update(context, data_dict)
