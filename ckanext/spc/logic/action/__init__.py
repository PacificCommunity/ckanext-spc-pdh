from . import get


def get_actions():
    actions = dict(
        spc_dcat_show=get.spc_dcat_show,
        spc_thematic_area_list=get.spc_thematic_area_list
    )
    return actions
