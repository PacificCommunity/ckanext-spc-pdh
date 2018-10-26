from ckantoolkit import get_validator

from ckanext.spc.schemas.gmd import *

def _default(value):
    return get_validator('default')(value)


def get_default_maintenance_schema():
    frequencies = [
        "annually",
        "asNeeded",
        "biannually",
        "continually",
        "daily",
        "irregular",
        "monthly",
        "notPlanned",
        "weekly",
        "unkown",
        "otherMaintenancePeriod",
    ]
    return {
        'description': [get_validator('ignore_empty')],
        'maintenance_update_frequency': [get_validator('OneOf')(frequencies)],
        '__extras': [get_validator('ignore')]
    }


def get_default_individual_name_schema():
    return {
        'given_name': [get_validator('ignore_empty')],
        'sur_name': [get_validator('ignore_empty')],
        '__extras': [get_validator('ignore')]
    }


def get_default_sampling_schema():
    return {
        'study_extent': [get_validator('ignore_empty'), unicode],
        'sampling_description': [get_validator('not_empty'), unicode],
        '__extras': [get_validator('ignore')],
    }


def get_default_methods_schema():
    return {
        'method_step': [get_validator('ignore_empty'), unicode],
        'sampling': [
            get_validator('ignore_empty'),
            get_validator('construct_sub_schema')('sampling')
        ],
        'quality_control': [get_validator('ignore_empty'), unicode],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_keyword_set_schema():
    return {
        'keyword': [
            get_validator('not_empty'),
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'keyword_thesaurus': [get_validator('not_empty')],
        '__extras': [get_validator('ignore')]
    }


def get_default_address_schema():
    return {
        'delivery_point': [get_validator('ignore_empty')],
        'city': [get_validator('ignore_empty')],
        'administrative_area': [get_validator('ignore_empty')],
        'postal_code': [get_validator('ignore_empty')],
        'country': [get_validator('ignore_empty')],
        '__extras': [get_validator('ignore')]
    }


def get_default_agent_schema():
    return {
        'organization_name': [
            get_validator('spc_ignore_missing_if_one_of')(
                'individual_name', 'position_name'
            ),
            get_validator('not_empty'),
            unicode,
        ],
        'individual_name': [
            get_validator('spc_ignore_missing_if_one_of')(
                'position_name', 'organization_name'
            ),
            get_validator('construct_sub_schema')('individual_name'),
            get_validator('ignore_empty')
        ],
        'position_name': [
            get_validator('spc_ignore_missing_if_one_of')(
                'individual_name', 'organization_name'
            ),
            get_validator('not_empty'),
            unicode,
        ],
        'address': [
            get_validator('construct_sub_schema')('address'),
            get_validator('ignore_empty'),
        ],
        'phone': [get_validator('ignore_empty'), unicode],
        'electronic_mail_address': [
            get_validator('ignore_missing'),
            get_validator('email_validator'),
        ],
        'online_url': [
            get_validator('ignore_missing'),
            get_validator('url_validator'),
        ],
        'user_id': [
            get_validator('ignore_empty'),
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings'),
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_coverage_schema():
    return {
        'geographic_coverage': [
            get_validator('not_empty'),
            get_validator('construct_sub_schema')('geographic_coverage'),
        ],
        'temporal_coverage': [
            get_validator('ignore_empty'),
            get_validator('construct_sub_schema')('temporal_coverage'),
        ],
        'taxonomic_coverage': [
            get_validator('not_empty'),
            get_validator('construct_sub_schema')('taxonomic_coverage'),
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_bounding_coordinates_schema():
    return {
        'west_bounding_coordinate': [
            get_validator('not_empty'),
            get_validator('spc_float_validator')
        ],
        'east_bounding_coordinate': [
            get_validator('not_empty'),
            get_validator('spc_float_validator')
        ],
        'north_bounding_coordinate': [
            get_validator('not_empty'),
            get_validator('spc_float_validator')
        ],
        'south_bounding_coordinate': [
            get_validator('not_empty'),
            get_validator('spc_float_validator')
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_geographic_coverage_schema():
    return {
        'geographic_description': [get_validator('not_empty'), unicode],
        'bounding_coordinates': [
            get_validator('not_empty'),
            get_validator('construct_sub_schema')('bounding_coordinates')
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_range_of_dates_schema():
    return {
        'begin_date': [
            get_validator('not_empty'),
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'end_date': [
            get_validator('not_empty'),
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_temporal_coverage_schema():
    return {
        'range_of_dates': [
            get_validator('spc_ignore_missing_if_one_of')('single_date_time'),
            get_validator('construct_sub_schema')('range_of_dates')
        ],
        'single_date_time': [
            get_validator('spc_ignore_missing_if_one_of')('range_of_dates'),
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_taxonomic_coverage_schema():
    return {
        'general_taxonomic_coverage': [get_validator('ignore_empty'), unicode],
        'taxonomic_classification': get_default_taxonomic_class_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_taxonomic_class_schema():
    return {
        'taxon_rank_name': [get_validator('ignore_empty'), unicode],
        'taxon_rank_value': [get_validator('not_empty'), unicode],
        'common_name': [get_validator('ignore_empty'), unicode],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_personnel_schema():
    return {
        'person': get_default_agent_with_role_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_project_schema():
    return {
        'title': [get_validator('not_empty'), unicode],
        'personnel': [
            get_validator('ignore_empty'),
            get_validator('construct_sub_schema')('personnel')
        ],
        'abstract': [get_validator('ignore_empty'), unicode],
        'funding': [get_validator('ignore_empty'), unicode],
        'study_area_description': [
            get_validator('ignore_empty'),
            get_validator('construct_sub_schema')('study_area_description')
        ],
        'design_description': [get_validator('ignore_empty'), unicode],
        'id': [get_validator('ignore_empty'), unicode],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_study_area_description_schema():
    return {
        'descriptor_value': [get_validator('not_empty'), unicode],
        'citable_classification_system': [get_validator('boolean_validator')],
        'name': [
            get_validator('ignore_empty'),
            get_validator('OneOf')(['thematic', 'geographic', 'generic'])
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_agent_with_role_schema():
    schema = get_default_agent_schema()
    schema['role'] = [
        get_validator('not_empty'),
        unicode,
    ]
    return schema
