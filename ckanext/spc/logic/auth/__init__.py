from . import get
from . import update
from . import delete
from . import create


def get_auth_functions():
    auth_functions = dict(
        spc_dcat_show=get.spc_dcat_show,
        spc_thematic_area_list=get.spc_thematic_area_list,
        resource_update=update.spc_resource_update,
        resource_create=create.spc_resource_create,
        resource_delete=delete.spc_resource_delete,
    )
    return auth_functions
