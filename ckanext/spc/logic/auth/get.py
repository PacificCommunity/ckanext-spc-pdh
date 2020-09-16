import ckan.plugins.toolkit as tk

from ckan.authz import is_authorized, is_sysadmin, has_user_permission_for_group_or_org
from ckan.logic import NotFound
from ckan.common import _

from ckanext.spc.model import AccessRequest


def spc_dcat_show(context, data_dict):
    return is_authorized('package_show', context, data_dict)


@tk.auth_allow_anonymous_access
def spc_thematic_area_list(context, data_dict=None):
    return is_authorized('site_read', context, data_dict)


@tk.chained_auth_function
def datastore_search_sql(up_func, context, data_dict):
    return is_authorized('sysadmin', context)


def get_access_request(context, data_dict):
    return is_authorized('site_read', context, data_dict)


def manage_access_requests(context, data_dict):
    if not context['user']:
        return {'success': False}

    is_sys = is_sysadmin(context['user'])
    is_member = _check_permission_for_org(context, data_dict)

    return {'success': is_sys or is_member}


def spc_download_tracking_list(context, data_dict):
    return manage_access_requests(context, data_dict)


def _check_permission_for_org(context, data_dict):
    org_id = data_dict.get('owner_org') or data_dict.get('id')
    authorized = has_user_permission_for_group_or_org(
        org_id, context['user'], 'manage_group')
    return authorized


def restrict_dataset_show(context, data_dict):
    if not context['user']:
        return {'success': False}

    is_member = _check_permission_for_org(context, data_dict)
    is_accessed = AccessRequest.check_access_to_dataset(
        context['user'],
        data_dict['id']
    )
    restricted = data_dict.get('access', None) == 'restricted'

    return {'success': is_member or is_accessed or not restricted}


def resource_view_show(context, data_dict):
    model = context['model']

    resource_view = model.ResourceView.get(data_dict['id'])
    if not resource_view:
        raise NotFound(_('Resource view not found, cannot check auth.'))

    package = context['package']
    return is_authorized('restrict_dataset_show', context, package.as_dict())
