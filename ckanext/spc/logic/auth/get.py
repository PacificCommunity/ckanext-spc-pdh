import ckan.plugins.toolkit as tk

from ckan.authz import is_authorized, get_user_id_for_username, has_user_permission_for_group_or_org
from ckan.model import Member
from ckan.authz import get_user_id_for_username
from ckan.logic import NotFound

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
    org_id = data_dict.get('owner_org') or data_dict.get('id')
    authorized = has_user_permission_for_group_or_org(
        org_id, context['user'], 'manage_group')
    return {'success': authorized}


def _check_admin_or_member(context, data_dict):
    session = context['session']
    user_id = get_user_id_for_username(context['user'])
    model = context['model']

    is_sys = is_sysadmin(context['user'])

    org_id = data_dict.get('owner_org') or data_dict.get('id')
    is_member = session.query(model.Member) \
        .filter_by(group_id=org_id, table_id=user_id) \
        .filter((model.Member.capacity == 'editor') | (model.Member.capacity == 'admin')) \
        .first()

    return any((is_sys, is_member))


def restrict_dataset_show(context, data_dict):
    if not context['user']:
        return {'success': False}

    org_id = data_dict.get('owner_org') or data_dict.get('id')
    is_admin_or_member = has_user_permission_for_group_or_org(
        org_id, context['user'], 'manage_group')
    is_accessed = AccessRequest.check_access_to_dataset(
        context['user'],
        data_dict['id']
    )

    authorized = is_admin_or_member or is_accessed
    return {'success': authorized}


def resource_view_show(context, data_dict):
    model = context['model']

    resource_view = model.ResourceView.get(data_dict['id'])
    if not resource_view:
        raise NotFound(_('Resource view not found, cannot check auth.'))

    package = context['package']
    return is_authorized('restrict_dataset_show', context, package.as_dict())
