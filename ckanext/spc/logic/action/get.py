import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h

import ckanext.scheming.helpers as scheming_helpers
import ckanext.spc.utils as utils

import math


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
