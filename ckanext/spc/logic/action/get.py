import ckan.plugins.toolkit as tk
import ckanext.spc.utils as utils


@tk.side_effect_free
def spc_dcat_show(context, data_dict):
    id = tk.get_or_bust(data_dict, 'id')
    tk.check_access('spc_dcat_show', context, data_dict)
    pkg_dict = tk.get_action('package_show')(context, data_dict)
    utils.normalize_to_dcat(pkg_dict)
    return pkg_dict
