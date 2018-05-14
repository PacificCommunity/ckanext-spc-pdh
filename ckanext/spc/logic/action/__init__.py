from . import get


def get_actions():
    actions = dict(
        spc_dcat_show=get.spc_dcat_show
    )
    return actions
