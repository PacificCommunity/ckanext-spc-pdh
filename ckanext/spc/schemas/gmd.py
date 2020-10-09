from ckantoolkit import get_validator
from ckan.lib.navl.validators import unicode_safe

ne = get_validator('not_empty')
im = get_validator('ignore_empty')


def _sub(name):
    return get_validator('construct_sub_schema')(name)


def get_default_gmd_citation_schema():
    return {
        'title': [ne, unicode_safe],
        'alternate_title': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'date': get_default_gmd_date_schema(),
        'edition': [im, unicode_safe],
        'edition_date': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'cited_responsible_party': get_default_gmd_cited_responsible_party_schema(),
        'presentation_form': get_default_gmd_code_string_schema(),
        'series': [im, _sub('gmd_series')],
        'other_citation_details': [im, unicode_safe],
        'collective_title': [im, unicode_safe],
        'isbn': [im, unicode_safe],
        'issn': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_identification_info_schema():
    return {
        "identification": [
            get_validator("not_empty"),
            _sub('gmd_base_identification')
        ],
        'spatial_representation_type': get_default_gmd_code_string_schema(),
        'spatial_resolution': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'language': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'character_set': get_default_gmd_code_string_schema(),
        'topic_category': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'environment_description': [im, unicode_safe],
        'extent': get_default_gmd_extent_schema(),
        'supplemental_information': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_extent_schema():
    return {
        'description': [im, unicode_safe],
        'geographic_element': [im, _sub('gmd_geo_element')],
        'vertical_element': [im, _sub('gmd_vertical_element')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_vertical_element_schema():
    return {
        'minimum_value': [ne, get_validator('spc_float_validator')],
        'maximum_value': [ne, get_validator('spc_float_validator')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_geo_element_schema():
    return {
        'extent_type_code': [im, get_validator('boolean_validator')],
        'bounding_box': [im, _sub('gmd_bounding_box')],
        'geographic_identifier': [im, _sub('gmd_identifier')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_bounding_box_schema():
    return {
        'west_bound_longitude': [ne, get_validator('spc_float_validator')],
        'east_bound_longitude': [ne, get_validator('spc_float_validator')],
        'south_bound_latitude': [ne, get_validator('spc_float_validator')],
        'north_bound_latitude': [ne, get_validator('spc_float_validator')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_base_identification_schema():
    return {
        'citation': [ne, _sub('gmd_citation')],
        'abstract': [ne, unicode_safe],
        'purpose': [im, unicode_safe],
        'credit': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'status': get_default_gmd_code_string_schema(),
        'point_of_contact': get_default_gmd_cited_responsible_party_schema(),
        'resource_maintenance': [
            get_validator('spc_list_of')(_sub('gmd_maintenance'))
        ],
        'graphic_overview': get_default_gmd_graphic_schema(),
        'resource_format': get_default_gmd_format_schema(),
        'descriptive_keywords': get_default_gmd_keywords_schema(),
        'resource_specific_usage': get_default_gmd_usage_schema(),
        'resource_constraints': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'aggregation_info': get_default_gmd_aggregation_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_aggregation_schema():
    return {
        'aggregate_data_set_name': [im, _sub('gmd_citation')],
        'aggregate_data_set_identifier': [im, _sub('gmd_identifier')],
        'association_type': [ne, _sub('gmd_code_string')],
        'initiative_type': [im, _sub('gmd_code_string')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_usage_schema():
    return {
        'specific_usage': [ne, unicode_safe],
        'usage_date_time': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'user_determined_limitations': [im, unicode_safe],
        'user_contact_info': _sub('gmd_cited_responsible_party'),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_keywords_schema():
    return {
        'keyword': [
            ne,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'type': [im, _sub('gmd_code_string')],
        'thesaurus_name': [im, _sub('gmd_citation')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_format_schema():
    return {
        'name': [ne, unicode_safe],
        'version': [ne, unicode_safe],
        'amendment_number': [im, unicode_safe],
        'specification': [im, unicode_safe],
        'file_decompression_technique': [im, unicode_safe],
        'format_distributor': [im, get_default_gmd_distributor_schema()],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_distributor_schema():
    return {
        'distributor_contact': [ne, _sub('gmd_cited_responsible_party')],
        'distribution_order_process': get_default_gmd_order_process_schema(),
        'distributor_transfer_options': get_default_gmd_transfer_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_transfer_schema():
    return {
        'units_of_distribution': [im, unicode_safe],
        'transfer_size': [im, get_validator('spc_float_validator')],
        'on_line': get_default_gmd_online_resource_schema(),
        'off_line': [im, _sub('gmd_offline_resource')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_order_process_schema():
    return {
        'fees': [im, unicode_safe],
        'planned_available_date_time': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'ordering_instructions': [im, unicode_safe],
        'turnaround': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_graphic_schema():
    return {
        'file_name': [ne, unicode_safe],
        'file_description': [im, unicode_safe],
        'file_type': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_maintenance_schema():
    return {
        'maintenance_and_update_frequency': [ne, _sub('gmd_code_string')],
        'date_of_next_update': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'user_defined_maintenance_frequency': [im, unicode_safe],
        'update_scope': get_default_gmd_code_string_schema(),
        'maintenance_note': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'contact': get_default_gmd_cited_responsible_party_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_date_schema():
    return {
        'date': [
            ne,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'date_type': [ne, _sub('gmd_code_string')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_code_string_schema():
    return {
        'code_list': [ne],
        'code_list_value': [ne],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_identifier_schema():
    return {
        'authority': [im, _sub('gmd_citation')],
        'code': [ne, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_cited_responsible_party_schema():
    return {
        'individual_name': [ne, unicode_safe],
        'organisation_name': [im, unicode_safe],
        'position_name': [im, unicode_safe],
        'contact_info': [im, _sub('gmd_contact')],
        'role': [ne, _sub('gmd_code_string')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_contact_schema():
    return {
        'phone': [im, _sub('gmd_phone')],
        'address': [im, _sub('gmd_address')],
        'online_resource': [im, _sub('gmd_online_resource')],
        'hours_of_service': [im, unicode_safe],
        'contact_instructions': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_online_resource_schema():
    return {
        'linkage': [ne, get_validator('url_validator')],
        'protocol': [im, unicode_safe],
        'application_profile': [im, unicode_safe],
        'name': [im, unicode_safe],
        'description': [im, unicode_safe],
        'function': [im, _sub('gmd_code_string')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_offline_resource_schema():
    return {
        'name': [im, _sub('gmd_code_string')],
        'density': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'density_units': [im, unicode_safe],
        'volumes': [im, get_validator('int_validator')],
        'medium_format': get_default_gmd_code_string_schema(),
        'medium_note': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_series_schema():
    return {
        'name': [im, unicode_safe],
        'issue_identification': [im, unicode_safe],
        'page': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_address_schema():
    return {
        'delivery_point': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'city': [im, unicode_safe],
        'administrative_area': [im, unicode_safe],
        'postal_code': [im, unicode_safe],
        'country': [im, unicode_safe],
        'electronic_mail_address': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_phone_schema():
    return {
        'voice': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'facsimile': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_locale_schema():
    return {
        'language_code': [ne, _sub('gmd_code_string')],
        'country': [im, _sub('gmd_code_string')],
        'character_encoding': [ne, _sub('gmd_code_string')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_spatial_schema():
    return {
        'vector': [im, _sub('gmd_vector_spatial')],
        'grid': [im, _sub('gmd_grid_spatial')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_grid_spatial_schema():
    return {
        'number_of_dimensions': [ne, get_validator('int_validator')],
        'axis_dimension_properties': get_default_gmd_geo_dimension_schema(),
        'cell_geometry': [ne, _sub('gmd_code_string')],
        'transformation_parameter_availability': [
            get_validator('boolean_validator')
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_geo_dimension_schema():
    return {
        'dimension_name': [ne, _sub('gmd_code_string')],
        'dimension_size': [ne, get_validator('int_validator')],
        'resolution': [im, get_validator('spc_float_validator')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_vector_spatial_schema():
    return {
        'topology_level': [im, _sub('gmd_code_string')],
        'geometric_objects': get_default_gmd_geo_object_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_geo_object_schema():
    return {
        'geometric_object_type': [ne, _sub('gmd_code_string')],
        'geometric_object_count': [im, get_validator('int_validator')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_metadata_extension_schema():
    return {
        'extension_on_line_resource': [im, _sub('gmd_online_resource')],
        'extended_element_information': [
            get_validator('spc_list_of')(_sub('gmd_extended_element')), im
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_extended_element_schema():
    return {
        'name': [ne, unicode_safe],
        'short_name': [im, unicode_safe],
        'domain_code': [im, get_validator('int_validator')],
        'definition': [ne, unicode_safe],
        'obligation': [im, unicode_safe],
        'condition': [im, unicode_safe],
        'data_type': [im, _sub('gmd_code_string')],
        'maximum_occurrence': [im, unicode_safe],
        'domain_value': [im, unicode_safe],
        'parent_entity': [
            ne,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'rule': [ne, unicode_safe],
        'rationale': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'source': get_default_gmd_cited_responsible_party_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_content_info_schema():
    return {
        'coverage_description': [im, _sub('gmd_coverage_description')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_coverage_description_schema():
    return {
        'attribute_description': [ne, unicode_safe],
        'content_type': [ne, _sub('gmd_code_string')],
        'dimension': get_default_gmd_range_dimension_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_range_dimension_schema():
    return {
        'sequence_identifier': [im, unicode_safe],
        'descriptor': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_data_quality_schema():
    return {
        'scope': [ne, _sub('gmd_dqt_scope')],
        'report': get_default_gmd_dqt_report_schema(),
        'lineage': [im, _sub('gmd_lineage')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_lineage_schema():
    return {
        'statement': [im, unicode_safe],
        'process_step': get_default_gmd_lineage_process_step_schema(),
        'source': get_default_gmd_lineage_source_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_lineage_process_step_schema():
    return {
        'description': [ne, unicode_safe],
        'rationale': [im, unicode_safe],
        'date_time': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'processor': [
            im,
            get_validator('spc_list_of')(_sub('gmd_cited_responsible_party'))
        ],
        'source': [
            im, get_validator('spc_list_of')(_sub('gmd_lineage_source'))
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_lineage_source_schema():
    return {
        'description': [im, unicode_safe],
        'scale_denominator': [im, get_validator('int_validator')],
        'source_reference_system': [im, _sub('gmd_identifier')],
        'source_citation': [im, _sub('gmd_citation')],
        'source_extent': get_validator('spc_list_of')(_sub('gmd_extent')),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_dqt_report_schema():
    return {
        'name_of_measure': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'measure_identification': [im, _sub('gmd_identifier')],
        'measure_description': [im, unicode_safe],
        'evaluation_method_type': [im, _sub('gmd_code_string')],
        'evaluation_method_description': [im, unicode_safe],
        'evaluation_procedure': [im, _sub('gmd_citation')],
        'date_time': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'result': [ne, _sub('gmd_dqt_result')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_dqt_result_schema():
    return {
        'specification': [ne, _sub('gmd_citation')],
        'explanation': [ne, unicode_safe],
        'pass': [get_validator('boolean_validator')],
        'error_statistic': [im, unicode_safe],
        'value': [
            ne,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_dqt_scope_schema():
    return {
        'level': [ne, _sub('gmd_code_string')],
        'extent': [im, _sub('gmd_extent')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_metadata_constraints_schema():
    return {
        'use_limitations': [
            ne,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_application_schema_info_schema():
    return {
        'name': [ne, _sub('gmd_citation')],
        'schema_language': [ne, unicode_safe],
        'constraint_language': [ne, unicode_safe],
        'schema_ascii': [im, unicode_safe],
        'graphics_file': [im, unicode_safe],
        'software_development_file': [im, unicode_safe],
        'software_development_file_format': [im, unicode_safe],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }
