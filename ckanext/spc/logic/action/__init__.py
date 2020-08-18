from . import get
from . import create
from . import update


def get_actions():
    actions = dict(
        spc_dcat_show=get.spc_dcat_show,
        spc_thematic_area_list=get.spc_thematic_area_list,
        five_star_rating=get.five_star_rating,
        spc_package_search=get.spc_package_search,

        get_access_request=get.get_access_request,
        get_access_requests_for_org=get.get_access_requests_for_org,
        get_access_requests_for_pkg=get.get_access_requests_for_pkg,

        create_access_request=create.create_access_request,
        
        approve_access=update.approve_access,
        reject_access=update.reject_access,
        update_access=update.update_access,
    )
    return actions
