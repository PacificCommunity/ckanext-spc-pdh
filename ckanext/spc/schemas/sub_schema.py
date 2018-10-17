from ckantoolkit import get_validator


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


def get_default_position_name_schema():
    return {
        'given_name': [get_validator('ignore_empty')],
        'sur_name': [get_validator('not_empty')],
        '__extras': [get_validator('ignore')]
    }


def get_default_sampling_schema():
    return {
        'study_extent': [get_validator('not_empty'), unicode],
        'sampling_description': [get_validator('not_empty'), unicode],
        '__extras': [get_validator('ignore')],
    }


def get_default_methods_schema():
    return {
        'method_step': [get_validator('not_empty'), unicode],
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
            get_validator('convert_to_list_if_string'),
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
            get_validator('construct_sub_schema')('position_name'),
            get_validator('not_empty')
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
            get_validator('convert_to_list_if_string'),
            get_validator('list_of_strings'),
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_project_schema():
    return {
        'title': [get_validator('not_empty'), unicode],
        'personnel': get_default_agent_with_role_schema(),
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
