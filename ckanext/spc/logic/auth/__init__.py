from . import get


def get_auth_functions():
    auth_functions = dict(
        spc_dcat_show=get.spc_dcat_show
    )
    return auth_functions
