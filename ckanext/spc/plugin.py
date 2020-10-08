import logging
import os
import json
import uuid
import hashlib
import re
import sqlalchemy as sa

from io import StringIO
from PIL import Image
from collections import OrderedDict
from six import string_types, ensure_binary

import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h

from ckan.lib.uploader import Upload as DefaultUpload
from ckan.lib.uploader import ResourceUpload
from ckan.lib.plugins import DefaultTranslation
from ckan.logic import check_access
from ckan.common import _
from ckan.common import config
from ckan.model.license import DefaultLicense, LicenseRegister, License

import ckanext.spc.helpers as spc_helpers
import ckanext.spc.utils as spc_utils
import ckanext.spc.logic.action as spc_action
import ckanext.spc.logic.auth as spc_auth
import ckanext.spc.validators as spc_validators

from ckanext.spc.views import blueprints
from ckanext.spc.cli import get_commnads
from ckanext.spc.model.drupal_user import DrupalUser
from ckanext.spc.ingesters import MendeleyBib

import ckanext.scheming.helpers as scheming_helpers

from ckanext.ingest.interfaces import IIngest
from ckanext.discovery.plugins.search_suggestions.interfaces import ISearchTermPreprocessor
from ckanext.harvest.model import HarvestObject, HarvestSource

logger = logging.getLogger(__name__)

new_order_facet_dict = {
    'topic': _('Topic'),
    'member_countries':  _('Member countries'),
    'organization': _('Organisations'),
    'tags': _('Tags'),
    'res_format': _('Formats'),
    'type': _('Dataset type'),
    'license_id': _('Licenses')
}

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


class Upload(DefaultUpload):
    def update_data_dict(self, data_dict, url_field, file_field, clear_field):
        '''
        Resize and optimize logo image before upload
        '''
        uploaded_file = data_dict.get('logo_upload')

        try:
            img = Image.open(uploaded_file)
        except (IOError, AttributeError):
            super(Upload, self).update_data_dict(data_dict, url_field, file_field, clear_field)
            return

        size = img.size
        while True:
            if size[0] < 350:
                break
            size = map(lambda x: int(x*0.75), size)

        img = img.resize(size, Image.LANCZOS)
        file = StringIO()

        format = uploaded_file.filename.split('.')[-1].upper()
        format = 'JPEG' if format == 'JPG' else 'PNG'

        try:
            img.save(file,
                 format=format,
                 optimize=True,
                 subsampling=0)
        except Exception:
            super(Upload, self).update_data_dict(data_dict, url_field, file_field, clear_field)

        data_dict['logo_upload'].stream = file

        super(Upload, self).update_data_dict(data_dict, url_field, file_field, clear_field)

class LocaleMiddleware(object):
    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['CKAN_LANG_IS_DEFAULT']:
            try:
                lang = environ.get('HTTP_ACCEPT_LANGUAGE', '').split(',')[0].split('-')[0]
                if len(lang) == 2:
                    environ['CKAN_LANG'] = lang
                else:
                    logger.error('Unknown locale <%s>', lang)
            except IndexError:
                pass
        return self.app(environ, start_response)

class SpcUserPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthenticator, inherit=True)
    plugins.implements(plugins.IConfigurer)

    _connection = None

    @staticmethod
    def _make_password():
        # create a hard to guess password
        out = ''
        for n in range(8):
            out += str(uuid.uuid4())
        return out

    @staticmethod
    def _sanitize_drupal_username(name):
        """Convert a drupal username (which can have spaces and other special characters) into a form that is valid in CKAN
        """
        # convert spaces and separators
        name = re.sub('[ .:/]', '-', name)
        # take out not-allowed characters
        name = re.sub('[^a-zA-Z0-9-_]', '', name).lower()
        # remove doubles
        name = re.sub('--', '-', name)
        # remove leading or trailing hyphens
        name = name.strip('-')[:99]
        return name

    @staticmethod
    def _drupal_session_name():
        server_name = toolkit.request.environ['HTTP_HOST']
        name = 'SSESS%s' % hashlib.sha256(ensure_binary(server_name)).hexdigest()[:32]
        return name

    @staticmethod
    def _save_drupal_user_id(ckan_user_id, drupal_user_id):
        user = DrupalUser.create_or_get_user(ckan_user_id, drupal_user_id)
        model.Session.commit()
        return user

    @staticmethod
    def _get_user(user_id, email):
        user = None

        if user_id:
            try:
                user = toolkit.get_action('user_show')(
                    {'return_minimal': True,
                    'keep_sensitive_data': True,
                    'keep_email': True},
                    {'id': user_id})
            except toolkit.ObjectNotFound:
                user = None

        if not user:
            try:
                user_id = model.Session.query(model.User.id) \
                               .filter(model.User.email==email) \
                               .first()[0]
                user = toolkit.get_action('user_show')(
                    {'return_minimal': True,
                    'keep_sensitive_data': True,
                    'keep_email': True},
                    {'id': user_id})

            except (toolkit.ObjectNotFound, TypeError):
                user = None

        return user

    def _login_user(self, user_data):
        # getting CKAN user if exists

        ckan_uid = DrupalUser.create_or_get_user(
            ckan_user=None,
            drupal_user=str(user_data.uid)
        )

        try:
            user_id = ckan_uid.ckan_user
        except AttributeError:
            user_id = None

        user = self._get_user(user_id, user_data.mail)

        # if we found user by email, we should "map" the ids
        if user and not user_id:
            self._save_drupal_user_id(user["id"], str(user_data.uid))

        if user:
            if user_data.mail != user['email']:
                user['email'] = user_data.mail

                user = toolkit.get_action('user_update')(
                                         {'ignore_auth': True,
                                         'user': ''},
                                         user)

            if user_data.name != user['name']:
                User = model.Session.query(model.User).get(user['id'])
                User.name = self._sanitize_drupal_username(user_data.name)
                model.Session.commit()
                # get user again after changes in user model
                user = self._get_user(user_id, user_data.mail)
        else:
            user = {'email': user_data.mail,
                    'name': self._sanitize_drupal_username(user_data.name),
                    'password': self._make_password()}

            user = toolkit.get_action('user_create')(
                                      {'ignore_auth': True,
                                      'user': ''},
                                      user)
            # save drupal user ID
            self._save_drupal_user_id(user["id"], str(user_data.uid))
        toolkit.c.user = user['name']

    # IAuthenticator

    def identify(self):
        """ This does drupal authorization.
        The drupal session contains the drupal id of the logged in user.
        We need to convert this to represent the ckan user. """

        # If no drupal session name create one
        drupal_sid = toolkit.request.cookies.get(self._drupal_session_name())

        if drupal_sid:
            engine = sa.create_engine(self._connection)
            user = engine.execute(
                'SELECT u.name, u.mail, u.uid '
                'FROM users u '
                'JOIN sessions s on s.uid=u.uid '
                'WHERE s.sid=%s',
                [str(drupal_sid)])

            user_data = user.first()
            # check if session has username,
            # otherwise is unauthenticated user session
            try:
                if user_data.name and user_data.name != '':
                    self._login_user(user_data)
            except AttributeError:
                pass

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'spc_user/templates')
        self._connection = config_.get('spc.drupal.db_url')

        if not self._connection:
            raise Exception('Drupal7 extension has not been configured')

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
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IUploader, inherit=True)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IUploader
    def get_uploader(self, upload_to, old_filename):
        return Upload(upload_to, old_filename)

    def get_resource_uploader(self, data_dict):
        return ResourceUpload(data_dict)

    # IBlueprint

    def get_blueprint(self):
        return blueprints

    # IIngest

    def get_ingesters(self):
        return [('mendeley_bib', MendeleyBib())]

    # IRouter

    def before_map(self, map):

        # CKAN login form can be accessed in the debug mode
        if not config.get('debug', False):
            map.redirect('/user/login', spc_helpers.get_drupal_user_url('login'))

        map.redirect('/user/register', spc_helpers.get_drupal_user_url('register'))
        map.redirect('/user/reset', '/')

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
        toolkit.add_ckan_admin_tab(config_, 'spc_admin.broken_links', 'Reports')

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'spc')

        conf_directive = 'spc.report.broken_links_filepath'
        if not config_.get(conf_directive):
            raise KeyError(
                'Please, specify `{}` inside your config file'.
                format(conf_directive)
            )


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
        search_params = spc_utils.params_into_advanced_search(search_params)
        return search_params

    def after_search(self, results, params):
        _org_cache = {}
        try:
            for item in results['search_facets']['type']['items']:
                item['display_name'] = toolkit._(item['display_name'])
        except KeyError:
            pass
        try:
            for item in results['search_facets']['member_countries']['items']:
                item['display_name'] = toolkit.h.spc_member_countries_facet_label(item)
        except KeyError:
            pass

        is_popular_first = toolkit.asbool(
            params.get('extras', {}).get('ext_popular_first', False))

        for item in results['results']:
            if len(item) == 1:
                # it's shortened search, probably initiated by bulk download
                continue
            item['tracking_summary'] = (
                model.TrackingSummary.get_for_package(item['id']))

            item['five_star_rating'] = spc_utils._get_stars_from_solr(
                item['id'])
            item['ga_view_count'] = spc_utils.ga_view_count(item['name'])
            item['short_notes'] = h.truncate(item.get('notes', ''))

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
        if plugins.plugin_loaded('ga-report'):
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

        if not plugins.plugin_loaded('harvest'):
            pkg_dict['isPartOf'] = 'pdh.pacificdatahub'
        elif _package_is_native(pkg_dict['id']):
            pkg_dict['isPartOf'] = 'pdh.pacificdatahub'
        else:
            src_type = _get_isPartOf(pkg_dict['id'])
            if src_type:
                pkg_dict['isPartOf'] = src_type

        if spc_helpers.is_restricted(pkg_dict):
            pkg_dict = spc_utils.delete_res_urls_if_restricted(context, pkg_dict)

        return pkg_dict

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        # facets_dict.pop('groups', None)
        # facets_dict['topic'] = _('Topic')
        # facets_dict['type'] = _('Dataset type')
        # facets_dict['member_countries'] = _('Member countries')

        facets_dict = new_order_facet_dict
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        # facets_dict.pop('groups', None)
        # facets_dict['topic'] = _('Topic')
        # facets_dict['type'] = _('Dataset type')
        # facets_dict['member_countries'] = _('Member countries')

        facets_dict = new_order_facet_dict
        return facets_dict
    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        # facets_dict.pop('groups', None)
        # facets_dict['topic'] = _('Topic')
        # facets_dict['type'] = _('Dataset type')
        # facets_dict['member_countries'] = _('Member countries')

        facets_dict = new_order_facet_dict
        return facets_dict


    # IClick
    def get_commands(self):
        return get_commnads()


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
