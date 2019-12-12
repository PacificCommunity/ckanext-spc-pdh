import logging
import os
import json
import textract

from collections import OrderedDict
from six import string_types

import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
from ckan.lib.plugins import DefaultTranslation
from ckan.common import _
import ckanext.scheming.helpers as scheming_helpers

import ckanext.spc.helpers as spc_helpers
import ckanext.spc.utils as spc_utils
import ckanext.spc.logic.action as spc_action
import ckanext.spc.logic.auth as spc_auth
import ckanext.spc.validators as spc_validators
import ckanext.spc.controllers.spc_package
from ckanext.spc.ingesters import MendeleyBib

from ckanext.harvest.model import HarvestObject, HarvestSource

from ckan.model.license import DefaultLicense, LicenseRegister, License

from ckanext.ingest.interfaces import IIngest
from ckanext.spc.views import blueprints

logger = logging.getLogger(__name__)


class LicenseCreativeCommonsNonCommercialShareAlice40(DefaultLicense):
    id = "cc-nc-sa-4.0"
    url = "https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode"

    @property
    def title(self):
        return _("Creative Commons Attribution-NonCommercial-ShareAlike 4.0")


class LicenseCreativeCommonsNonCommercial40(DefaultLicense):
    id = "cc-nc-4.0"
    url = "https://creativecommons.org/licenses/by-nc/4.0/legalcode"

    @property
    def title(self):
        return _("Creative Commons Attribution-NonCommercial 4.0")


class LicenseSprepPublic(DefaultLicense):
    id = "sprep-public-license"
    url = ("https://pacific-data.sprep.org/dataset/"
           "data-portal-license-agreements/resource/"
           "de2a56f5-a565-481a-8589-406dc40b5588")

    @property
    def title(self):
        return _("SPREP Public License")


original_create_license_list = LicenseRegister._create_license_list


def _redefine_create_license_list(self, *args, **kwargs):
    original_create_license_list(self, *args, **kwargs)
    self.licenses.append(License(LicenseCreativeCommonsNonCommercial40()))
    self.licenses.append(
        License(LicenseCreativeCommonsNonCommercialShareAlice40()))
    self.licenses.append(License(LicenseSprepPublic()))


LicenseRegister._create_license_list = _redefine_create_license_list


class SpcPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(IIngest)
    plugins.implements(plugins.IBlueprint)


    # IBlueprint
    def get_blueprint(self):
        return blueprints

    # IIngest

    def get_ingesters(self):
        return [('mendeley_bib', MendeleyBib())]

    # IRouter

    def after_map(self, map):
        map.connect('spc_dataset.new',
                    '/{package_type}/new',
                    controller='package',
                    action='new')

        map.connect(
            'spc_dataset.choose_type',
            '/dataset/new/choose_type',
            controller='ckanext.spc.controllers.spc_package:PackageController',
            action='choose_type')

        return map

    def before_map(self, map):

        map.connect('search_queries.index',
                    '/ckan-admin/search-queries',
                    controller=('ckanext.spc.controllers.search_queries'
                                ':SearchQueryController'),
                    action='index',
                    ckan_icon='search-plus')

        return map

    # IConfigurable

    def configure(self, config_):
        self.dataset_types = OrderedDict([
            (schema['dataset_type'], schema['about'])
            for schema in scheming_helpers.scheming_dataset_schemas().values()
        ])
        self.member_countries = OrderedDict([
            (choice['value'], choice['label'])
            for choice in scheming_helpers.scheming_get_preset(
                'member_countries')['choices']
        ])

        filepath = os.path.join(os.path.dirname(__file__), 'data/eez.json')
        if os.path.isfile(filepath):
            with open(filepath) as file:
                logger.debug('Updating EEZ list')
                collection = json.load(file)
                spc_utils.eez.update(collection['features'])

        toolkit.add_ckan_admin_tab(config_, 'search_queries.index',
                                   'Search Queries')
        toolkit.add_ckan_admin_tab(config_, 'ingest.index', 'Ingest')

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'spc')

    # ITemplateHelpers

    def get_helpers(self):
        helpers = {
            'spc_dataset_type_label':
            lambda type: self.dataset_types.get(type),
            'spc_type_facet_label':
            lambda item: self.dataset_types.get(item['display_name'], item[
                'display_name']),
            'spc_member_countries_facet_label':
            lambda item: self.member_countries.get(
                item['display_name'].upper(), item['display_name'])
        }
        helpers.update(spc_helpers.get_helpers())
        return helpers

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

    def before_search(self, search_params):
        fq = search_params.get('fq')
        if isinstance(fq, string_types):
            search_params['fq'] = fq.replace(
                'dataset_type:dataset', 'dataset_type:({})'.format(' OR '.join(
                    [type for type in self.dataset_types])))
        return search_params

    def after_search(self, results, params):
        _org_cache = {}

        is_popular_first = toolkit.asbool(
            params.get('extras', {}).get('ext_popular_first', False))

        for item in results['results']:
            item['tracking_summary'] = (
                model.TrackingSummary.get_for_package(item['id']))

            item['five_star_rating'] = spc_utils._get_stars_from_solr(
                item['id'])
            item['ga_view_count'] = spc_utils.ga_view_count(item['name'])
            item['short_notes'] = h.whtext.truncate(item.get('notes', ''))

            org_name = item['organization']['name']
            try:
                organization = _org_cache[org_name]
            except KeyError:
                organization = h.get_organization(org_name)
                _org_cache[org_name] = organization
            item['organization_image_url'] = organization.get(
                'image_display_url') or h.url_for_static(
                    '/base/images/placeholder-organization.png',
                    qualified=True)
            if _package_is_native(item['id']):
                item['isPartOf'] = 'pdh.pacificdatahub'
            else:
                src_type = _get_isPartOf(item['id'])
                if src_type:
                    item['isPartOf'] = src_type


        if is_popular_first:
            results['results'].sort(key=lambda i: i.get('ga_view_count', 0),
                                    reverse=True)

        spc_utils.store_search_query(params)

        return results

    def before_index(self, pkg_dict):
        pkg_dict['extras_ga_view_count'] = spc_utils.ga_view_count(
            pkg_dict['name'])

        topic_str = pkg_dict.get('thematic_area_string', '[]')
        if isinstance(topic_str, string_types):
            pkg_dict['topic'] = json.loads(topic_str)
        else:
            pkg_dict['topic'] = topic_str

        pkg_dict.update(
            extras_five_star_rating=spc_utils.count_stars(pkg_dict))
        if isinstance(pkg_dict.get('member_countries', '[]'), string_types):
            pkg_dict['member_countries'] = spc_helpers.countries_list(
                pkg_dict.get('member_countries', '[]'))
        # Otherwise you'll get `immense field` error from SOLR
        pkg_dict.pop('data_quality_info', None)

        return pkg_dict

    def after_show(self, context, pkg_dict):
        pkg_dict['five_star_rating'] = spc_utils._get_stars_from_solr(
            pkg_dict['id'])

        if _package_is_native(pkg_dict['id']):
            pkg_dict['isPartOf'] = 'pdh.pacificdatahub'
        else:
            src_type = _get_isPartOf(pkg_dict['id'])
            if src_type:
                pkg_dict['isPartOf'] = src_type
        return pkg_dict

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        facets_dict.pop('groups', None)
        facets_dict['topic'] = _('Topic')
        facets_dict['type'] = _('Dataset type')
        facets_dict['member_countries'] = _('Member countries')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        facets_dict.pop('groups', None)
        facets_dict['topic'] = _('Topic')
        facets_dict['type'] = _('Dataset type')
        facets_dict['member_countries'] = _('Member countries')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        facets_dict.pop('groups', None)
        facets_dict['topic'] = _('Topic')
        facets_dict['type'] = _('Dataset type')
        facets_dict['member_countries'] = _('Member countries')
        return facets_dict


def _package_is_native(id):
    return not model.Session.query(HarvestObject).filter(
        HarvestObject.package_id == id).first()

def _get_isPartOf(id):
    src_id = model.Session.query(HarvestObject.harvest_source_id) \
                             .filter(HarvestObject.package_id == id) \
                             .first()[0]
    config = model.Session.query(HarvestSource.config) \
                          .filter(HarvestSource.id == src_id) \
                          .first()[0]
    if config:
        return json.loads(config).get('isPartOf')
