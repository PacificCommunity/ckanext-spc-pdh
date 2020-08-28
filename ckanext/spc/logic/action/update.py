from ckan.model import Package, User
from ckan.common import config
from ckan.logic import get_or_bust, check_access
from ckan.plugins.toolkit import ObjectNotFound

from ckanext.spc.model import AccessRequest
from ckanext.spc.utils import notify_user
from ckanext.spc.utils import get_package_by_id_or_bust


def _reject_or_approve(context, data_dict, state):
    user = data_dict.get('user')
    request_id = data_dict.get('request_id')
    reject_reason = data_dict.get('reject_reason')

    if not context.get('ignore_auth'):
        check_access('manage_access_requests', context, data_dict)

    if request_id:
        access_request = AccessRequest.get_by_id(request_id)
        if access_request:
            pkg = get_package_by_id_or_bust({'id': access_request.package_id})
    else:
        pkg = get_package_by_id_or_bust(data_dict)
        access_request = AccessRequest.get(user, pkg.id)

    if not access_request:
        raise ObjectNotFound

    req = AccessRequest.set_access_request_state(
        user_id=user,
        package_id=pkg.id,
        state=state,
        reason=reject_reason,
        request_id=request_id
    )

    _notify_on_state_change(req)
    return req.as_dict()


def _notify_on_state_change(request):
    data_dict = _prepare_data_for_email(request)
    send_user_notifications = config.get(
        'spc.access_request.send_user_notification')

    if send_user_notifications and not request.is_pending:
        notify_user(data_dict['user'], request.state, data_dict)


def _prepare_data_for_email(request):
    pkg_obj = _get_package_obj(request.package_id)
    user_obj = _get_user_obj(request.user_id)
    timeout = config.get('spc.access_request.request_timeout', 3)

    return {'pkg': pkg_obj, 'user': user_obj,
            'reason': request.reason, 'timeout': timeout}


def _get_user_obj(username):
    user = User.get(username)
    if not user:
        raise ObjectNotFound()
    return user


def _get_package_obj(package_id):
    pkg = Package.get(package_id)
    if not pkg:
        raise ObjectNotFound
    return pkg


def approve_access(context, data_dict):
    return _reject_or_approve(context, data_dict, 'approved')


def update_access(context, data_dict):
    return _reject_or_approve(context, data_dict, 'pending')


def reject_access(context, data_dict):
    return _reject_or_approve(context, data_dict, 'rejected')
