import logging
import os
import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h

import ckanext.spc.helpers as spc_helpers
import ckanext.spc.utils as spc_utils
import ckanext.spc.logic.action as spc_action
import ckanext.spc.logic.auth as spc_auth
import ckanext.spc.validators as spc_validators

logger = logging.getLogger(__name__)


class SpcPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurable

    def configure(self, config_):
        filepath = os.path.join(os.path.dirname(__file__), 'data/eez.json')
        if not os.path.isfile(filepath):
            return
        with open(filepath) as file:
            logger.debug('Updating EEZ list')
            collection = json.load(file)
            spc_utils.eez.update(collection['features'])

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'spc')

    # ITemplateHelpers

    def get_helpers(self):
        return spc_helpers.get_helpers()

    # IActions

    def get_actions(self):
        return spc_action.get_actions()

    # IAuthFunctions

    def get_auth_functions(self):
        return spc_auth.get_auth_functions()

    # IValidators

    def get_validators(self):
        return spc_validators.get_validators()

    # IPackageController

    def after_search(self, results, params):
        _org_cache = {}

        is_popular_first = toolkit.asbool(
            params.get('extras', {}).get('ext_popular_first', False)
        )

        for item in results['results']:
            item['five_star_rating'] = spc_utils._get_stars_from_solr(item['id'])
            item['ga_view_count'] = spc_utils.ga_view_count(item['name'])
            item['short_notes'] = h.whtext.truncate(item['notes'])

            org_name = item['organization']['name']
            try:
                organization = _org_cache[org_name]
            except KeyError:
                organization = h.get_organization(org_name)
                _org_cache[org_name] = organization
            item['organization_image_url'
                 ] = organization.get('image_display_url') or h.url_for_static(
                     '/base/images/placeholder-organization.png',
                     qualified=True
                 )

        if is_popular_first:
            results['results'].sort(
                key=lambda i: i.get('ga_view_count', 0), reverse=True
            )
        return results

    def before_index(self, pkg_dict):
        pkg_dict['extras_ga_view_count'] = spc_utils.ga_view_count(
            pkg_dict['name']
        )
        pkg_dict.update(
            extras_five_star_rating=spc_utils.count_stars(pkg_dict)
        )
        return pkg_dict

    def after_show(self, context, pkg_dict):
        pkg_dict['five_star_rating'] = spc_utils._get_stars_from_solr(
            pkg_dict['id']
        )
        return pkg_dict
