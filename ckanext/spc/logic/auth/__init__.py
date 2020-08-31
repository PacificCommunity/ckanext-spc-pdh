from . import get
from . import update
from . import delete
from . import create



def get_auth_functions():
    auth_functions = dict(
#        datastore_search_sql=get.datastore_search_sql,
        spc_dcat_show=get.spc_dcat_show,
        spc_thematic_area_list=get.spc_thematic_area_list,
        resource_update=update.spc_resource_update,
        resource_create=create.spc_resource_create,
        # resource_delete=delete.spc_resource_delete,

        get_access_request=get.get_access_request,
        manage_access_requests=get.manage_access_requests,
        spc_download_tracking_list=get.spc_download_tracking_list,

        create_access_request=create.create_access_request,
        restrict_dataset_show=get.restrict_dataset_show,
        resource_view_show=get.resource_view_show,
    )
    return auth_functions
