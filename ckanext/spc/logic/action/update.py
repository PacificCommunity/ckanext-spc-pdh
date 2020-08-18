from ckan.model import Package, User
from ckan.common import config
from ckan.logic import get_or_bust, check_access
from ckan.plugins.toolkit import ObjectNotFound

from ckanext.spc.model import AccessRequest
from ckanext.spc.utils import notify_user


def _get_package_by_id(data_dict):
    pkg_id_or_name = get_or_bust(data_dict, 'id')
    # check if the package with such id exists to use it's ID

    pkg = Package.get(pkg_id_or_name)

    if not pkg:
        raise ObjectNotFound()
    return pkg


def _get_user_obj(username):
    user = User.get(username)

    if not user:
        raise ObjectNotFound()

    return user


def _reject_or_approve(context, data_dict, state):
    user = get_or_bust(data_dict, 'user')
    req_id = data_dict.get('req_id')
    reject_reason = data_dict.get('reject_reason')
    
    if not context.get('ignore_auth'):
        check_access('manage_access_requests', context, data_dict)

    if req_id:
        pkg_id = AccessRequest.get_by_id(req_id).package_id
        pkg = _get_package_by_id({'id': pkg_id})
    else:
        pkg = _get_package_by_id(data_dict)

    req = AccessRequest.set_access_request_state(
        user_id=user,
        package_id=pkg.id,
        state=state,
        reason=reject_reason,
        req_id=req_id
    )

    user_obj = _get_user_obj(user)
    if config.get('spc.access_request.send_user_notification') and req.state != 'pending':
        notify_user(user_obj, state, {'pkg': pkg,
                                      'user': user_obj,
                                      'reason': reject_reason})
    return req.as_dict()


def approve_access(context, data_dict):
    return _reject_or_approve(context, data_dict, 'approved')

def update_access(context, data_dict):
    return _reject_or_approve(context, data_dict, 'pending')

def reject_access(context, data_dict):
    return _reject_or_approve(context, data_dict, 'rejected')
