import ckan.plugins.toolkit as tk
import ckanext.spc.utils as utils
import ckanext.scheming.helpers as scheming_helpers


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
