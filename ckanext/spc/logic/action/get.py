import math

import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model

from ckan.model import Package
from ckan.authz import get_user_id_for_username

import ckanext.scheming.helpers as scheming_helpers
import ckanext.spc.utils as utils

from ckanext.spc.utils import get_package_by_id_or_bust
from ckanext.spc.model import AccessRequest, DownloadTracking

_get_or_bust = logic.get_or_bust
_check_access = logic.check_access


@tk.side_effect_free
def spc_dcat_show(context, data_dict):
    tk.get_or_bust(data_dict, 'id')
    tk.check_access('spc_dcat_show', context, data_dict)
    pkg_dict = tk.get_action('package_show')(context, data_dict)
    utils.normalize_to_dcat(pkg_dict)
    return pkg_dict


@tk.side_effect_free
@tk.auth_allow_anonymous_access
def spc_thematic_area_list(context, data_dict):
    tk.check_access('spc_thematic_area_list', context, data_dict)
    schema = scheming_helpers.scheming_get_dataset_schema('dataset')
    field = scheming_helpers.scheming_field_by_name(
        schema['dataset_fields'], 'thematic_area_string'
    )
    choices = scheming_helpers.scheming_field_choices(field)
    return choices


def five_star_rating(context, data_dict):
    '''5-star rating assignment.

    Open licenses: {licenses}
    Stars per format: {formats}

    :param url: URL of dataset(must be available via web)
    :type url: str
    :param license: one of open licenses
    :type license: string
    :param resources: list of dicts with `url` and `format`
    :type resources: list
    :param notes: data description
    :type notes: str

    :rtype: int
    '''

    url, license, notes = tk.get_or_bust(
        data_dict, ['url', 'license', 'notes']
    )
    resources = data_dict.get('resources', [])
    rating = 0

    # Open license is required
    license = license.lower()
    if not any(item in license for item in utils.open_licenses):
        return {'rating': 0}

    # At leas one link must be available
    resources = [res for res in resources if utils.check_link(res['url'])]
    if not resources and not utils.check_link(url):
        return {'rating': 0}
    for i in (4, 3, 2):
        if any(
            res['format'].lower() in utils.structured_formats[i]
            for res in resources
        ):
            rating = i
            break
    else:
        return {'rating': 1}

    has_links = any(
        check.search(notes)
        for check in (h.RE_MD_EXTERNAL_LINK, h.RE_MD_INTERNAL_LINK)
    )
    # 5 stars for linked data
    if has_links:
        return {'rating': 5}
    return {'rating': rating}


five_star_rating.__doc__ = five_star_rating.__doc__.format(
    licenses=utils.open_licenses, formats=utils.structured_formats
)


@tk.side_effect_free
def spc_package_search(context, data_dict):
    default_limit_rows = 1000
    revice_all_data = False

    if 'rows' not in data_dict:
        data_dict['rows'] = default_limit_rows
        revice_all_data = True

    types_count = {}

    def _countTypes(item):
        if item['type'] not in types_count:
            types_count[item['type']] = 1
        else:
            types_count[item['type']] += 1
        return True

    results = tk.get_action('package_search')(context, data_dict)

    if revice_all_data and results and results['count'] > 1000:
        extra_requests_number = int(math.ceil(
            results['count'] / 1000.0)) - 1
        for i in range(1, extra_requests_number + 1):
            offset = i * 1000
            data_dict['start'] = offset
            extra_request = tk.get_action('package_search')(
                context, data_dict)
            if extra_request and extra_request['results']:
                results['results'] += extra_request['results']

    map(_countTypes, results['results'])
    results['types_count'] = types_count

    return results


@tk.side_effect_free
def get_access_requests_for_pkg(context, data_dict):
    """
    returns the list of all access requests for a package
    """
    pkg = get_package_by_id_or_bust(data_dict)

    _check_access('manage_access_requests', context,
                  {'owner_org': pkg.owner_org})

    state = data_dict.get('state')

    return _dictize_access_requests_list(pkg.id, state, package=True)


@tk.side_effect_free
def get_access_requests_for_org(context, data_dict):
    """
    returns the list of all access requests for an organization
    """
    org_id = _get_or_bust(data_dict, 'id')
    _check_access('manage_access_requests', context, data_dict)
    state = data_dict.get('state')

    return _dictize_access_requests_list(org_id, state)


def _dictize_access_requests_list(_id, state, package=False):
    if package:
        reqs = AccessRequest.get_access_requests_for_pkg(_id, state)
    else:
        reqs = AccessRequest.get_access_requests_for_org(_id, state)

    return [req.as_dict() for req in reqs]


@tk.side_effect_free
def get_access_request(context, data_dict):
    user = _get_or_bust(data_dict, 'user')
    # check if the package with such id exists to use it's ID
    pkg = get_package_by_id_or_bust(data_dict)

    _check_access('get_access_request', context, data_dict)

    req = AccessRequest.get(user_id=user, package_id=pkg.id)
    if req:
        return req.as_dict()


@tk.side_effect_free
def spc_download_tracking_list(context, data_dict):
    id = tk.get_or_bust(data_dict, 'id')
    _check_access('spc_download_tracking_list', context, data_dict)
    pkg = model.Package.get(id)
    limit = tk.asint(data_dict.get('limit', 20))
    offset = tk.asint(data_dict.get('offset', 0))
    query = DownloadTracking.query(id=pkg.id)

    total = query.count()
    query = query.offset(offset).limit(limit)

    results = [
        {
            'package_id': resource.package_id,
            'user': user.name,
            'resource_id': resource.id,
            'resource_name': resource.name,
            'downloaded_at': track.downloaded_at.isoformat()
        }
        for (track, resource, user) in query
    ]
    return {
        'results': results,
        'count': total
    }
