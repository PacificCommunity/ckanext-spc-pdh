from . import get



def get_auth_functions():
    auth_functions = dict(
        datastore_search_sql=get.datastore_search_sql,
        spc_dcat_show=get.spc_dcat_show,
        spc_thematic_area_list=get.spc_thematic_area_list
    )
    return auth_functions
