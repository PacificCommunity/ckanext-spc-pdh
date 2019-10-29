from . import get


def get_auth_functions():
    auth_functions = dict(
        spc_dcat_show=get.spc_dcat_show,
        spc_thematic_area_list=get.spc_thematic_area_list
    )
    return auth_functions
