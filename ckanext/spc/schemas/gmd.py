from ckantoolkit import get_validator
from ckan.lib.navl.validators import unicode_safe

ne = get_validator('not_empty')
im = get_validator('ignore_empty')


def _sub(name):
    return get_validator('construct_sub_schema')(name)


def get_default_gmd_citation_schema():
    return {
        'title': [ne, str],
        'alternate_title': [
            im,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'date': get_default_gmd_date_schema(),
        'edition': [im, str],
        'edition_date': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'cited_responsible_party': get_default_gmd_cited_responsible_party_schema(),
        'presentation_form': get_default_gmd_code_string_schema(),
        'series': [im, _sub('gmd_series')],
        'other_citation_details': [im, str],
        'collective_title': [im, str],
        'isbn': [im, str],
        'issn': [im, str],
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
        'environment_description': [im, str],
        'extent': get_default_gmd_extent_schema(),
        'supplemental_information': [im, str],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_extent_schema():
    return {
        'description': [im, str],
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
        'abstract': [ne, str],
        'purpose': [im, str],
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
        'specific_usage': [ne, str],
        'usage_date_time': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'user_determined_limitations': [im, str],
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
        'name': [ne, str],
        'version': [ne, str],
        'amendment_number': [im, str],
        'specification': [im, str],
        'file_decompression_technique': [im, str],
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
        'units_of_distribution': [im, str],
        'transfer_size': [im, get_validator('spc_float_validator')],
        'on_line': get_default_gmd_online_resource_schema(),
        'off_line': [im, _sub('gmd_offline_resource')],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_order_process_schema():
    return {
        'fees': [im, str],
        'planned_available_date_time': [
            im,
            get_validator('spc_normalize_date'),
            get_validator('isodate'),
            get_validator('convert_to_json_if_date'),
        ],
        'ordering_instructions': [im, str],
        'turnaround': [im, str],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_graphic_schema():
    return {
        'file_name': [ne, str],
        'file_description': [im, str],
        'file_type': [im, str],
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
        'user_defined_maintenance_frequency': [im, str],
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
        'code': [ne, str],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_cited_responsible_party_schema():
    return {
        'individual_name': [ne, str],
        'organisation_name': [im, str],
        'position_name': [im, str],
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
        'hours_of_service': [im, str],
        'contact_instructions': [im, str],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_online_resource_schema():
    return {
        'linkage': [ne, get_validator('url_validator')],
        'protocol': [im, str],
        'application_profile': [im, str],
        'name': [im, str],
        'description': [im, str],
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
        'density_units': [im, str],
        'volumes': [im, get_validator('int_validator')],
        'medium_format': get_default_gmd_code_string_schema(),
        'medium_note': [im, str],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_series_schema():
    return {
        'name': [im, str],
        'issue_identification': [im, str],
        'page': [im, str],
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
        'city': [im, str],
        'administrative_area': [im, str],
        'postal_code': [im, str],
        'country': [im, str],
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
        'name': [ne, str],
        'short_name': [im, str],
        'domain_code': [im, get_validator('int_validator')],
        'definition': [ne, str],
        'obligation': [im, str],
        'condition': [im, str],
        'data_type': [im, _sub('gmd_code_string')],
        'maximum_occurrence': [im, str],
        'domain_value': [im, str],
        'parent_entity': [
            ne,
            get_validator('spc_to_json'),
            get_validator('convert_to_json_if_string'),
            get_validator('list_of_strings')
        ],
        'rule': [ne, str],
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
        'attribute_description': [ne, str],
        'content_type': [ne, _sub('gmd_code_string')],
        'dimension': get_default_gmd_range_dimension_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_range_dimension_schema():
    return {
        'sequence_identifier': [im, str],
        'descriptor': [im, str],
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
        'statement': [im, str],
        'process_step': get_default_gmd_lineage_process_step_schema(),
        'source': get_default_gmd_lineage_source_schema(),
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }


def get_default_gmd_lineage_process_step_schema():
    return {
        'description': [ne, str],
        'rationale': [im, str],
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
        'description': [im, str],
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
        'measure_description': [im, str],
        'evaluation_method_type': [im, _sub('gmd_code_string')],
        'evaluation_method_description': [im, str],
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
        'explanation': [ne, str],
        'pass': [get_validator('boolean_validator')],
        'error_statistic': [im, str],
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
        'schema_language': [ne, str],
        'constraint_language': [ne, str],
        'schema_ascii': [im, str],
        'graphics_file': [im, str],
        'software_development_file': [im, str],
        'software_development_file_format': [im, str],
        '__extras': [get_validator('ignore')],
        '__junk': [get_validator('ignore')],
    }
