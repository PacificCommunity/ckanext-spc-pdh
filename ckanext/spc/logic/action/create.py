from ckan.logic import get_or_bust, check_access
from ckan.common import config
from ckan.model import Package
from ckan.plugins.toolkit import ObjectNotFound

from ckanext.spc.model import AccessRequest
from ckanext.spc.utils import notify_org_members


def create_access_request(context, data_dict):
    if not context.get('ignore_auth'):
        check_access('create_access_request', context, data_dict)

    pkg_id_or_name, reason, user = get_or_bust(
        data_dict, ['id', 'reason', 'user'])
    user_org = data_dict.get('user_org')

    # check if the package with such id exists to use it's ID
    pkg = Package.get(pkg_id_or_name)

    if not pkg:
        raise ObjectNotFound()

    req = AccessRequest.create_or_get_request(
        user_id=user,
        package_id=pkg.id,
        reason=reason,
        org_id=pkg.owner_org
    )

    # send email notifications to org custodians
    if config.get('spc.access_request.send_admin_notification'):
        notify_org_members(pkg.owner_org,
                           {'pkg': pkg, 'user': user,
                            'reason': reason, 'user_org': user_org})

    return req.as_dict()
