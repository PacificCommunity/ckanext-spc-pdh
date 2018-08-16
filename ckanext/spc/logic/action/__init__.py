from . import get


def get_actions():
    actions = dict(
        spc_dcat_show=get.spc_dcat_show,
        spc_thematic_area_list=get.spc_thematic_area_list,
        five_star_rating=get.five_star_rating,
    )
    return actions
