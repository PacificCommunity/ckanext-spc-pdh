import logging
import os
import tempfile
import requests
import re

from smtplib import SMTPServerDisconnected
from operator import attrgetter, itemgetter

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic

from ckan.common import config
from ckan.lib.search import query_for
from ckan.lib.uploader import get_resource_uploader
from ckan.lib import mailer

from ckanext.ga_report.ga_model import GA_Url
from ckanext.spc.model import SearchQuery, DownloadTracking

logger = logging.getLogger(__name__)

open_licenses = [
    "cc", "creative commons", "open data commons", "pddl", "odc", "odbl",
    "against drm", "data licence germany", "design science license",
    "eff open audio license", "fal", "free art license",
    "gnu free documentation license", "gnu fdl", "miros license",
    "open government", "talis community license"
]

structured_formats = {
    2: ["xls", "xlsx", "mdb", "esri rest", "excel"],
    3: [
        "csv", "comma separated values", "tsv", "tab separated values", "wms",
        "web mapping service", "geojson", "wfs", "web feature service", "kml",
        "kmz", "json", "xml", "shp", "rss", "gpx"
    ],
    4: [
        "csv geo au", "sparql", "rdf", "relational document format", "json ld"
    ]
}


def _get_stars_from_solr(id):
    results = query_for('package').run({
        'q': 'id:' + id,
        'fl': 'extras_five_star_rating'
    })['results']
    try:
        return int(results[0]['extras']['five_star_rating'])
    except Exception as e:
        logger.warn('Unable to get rating of <{}>: {}'.format(id, e))
        return 0


def check_link(url):
    try:
        if not h.url_is_local(url):
            requests.head(url, timeout=2).raise_for_status()
    except Exception:
        return False
    return True


def count_stars(pkg_dict):
    """Count stars as per https://5stardata.info
    """
    resources = [{
        'format': res.get('format'),
        'url': res['url']
    } for res in pkg_dict.get('resources', [])]
    if not resources:
        resources = [
            {
                'format': format,
                'url': url
            } for (url, format) in
            zip(pkg_dict.get('res_url', []), (pkg_dict.get('res_format', [])))
        ]

    text = '\n'.join(
        filter(
            None,
            [pkg_dict.get('notes')] + pkg_dict.get('res_description', []) + [
                res['description']
                for res in pkg_dict.get('resources', [])
                if res.get('description')
            ]
        )
    )

    license = model.Package.get_license_register().get(
        pkg_dict.get('license_id')
    )
    is_open = license and license.isopen()
    license_id = license and license.id

    data_dict = dict(
        url=h.url_for(
            'dataset.read',
            id=pkg_dict['id'],
            qualified=True
        ),
        license='cc' if is_open else (license_id or ''),
        notes=text,
        resources=resources,
    )
    return tk.get_action('five_star_rating')(None, data_dict)['rating']


def _normalize_res(res):
    return {
        'title': res.get('name'),
        'description': res.get('description'),
        'format': res.get('format'),
        'byteSize': res.get('size'),
        'accessURL': res.get('url')
    }


def normalize_to_dcat(pkg_dict):
    pkg_dict['identifier'] = pkg_dict.pop('id')
    pkg_dict['description'] = pkg_dict.pop('notes', '')
    pkg_dict['landingPage'] = h.url_for(
        'dataset.read', id=pkg_dict['name'], qualified=True
    )
    pkg_dict['keyword'] = [tag['name'] for tag in pkg_dict.pop('tags', [])]

    pkg_dict['distribution'] = [
        _normalize_res(res) for res in pkg_dict.pop('resources', [])
    ]

    pkg_dict['publisher'] = dict(
        name=pkg_dict.pop('publisher', ''),
        mbox=pkg_dict.pop('publisher_email', '')
    )

    pkg_dict['contactPoint'] = pkg_dict.get('contact', '')
    if pkg_dict.get('contact_email'):
        pkg_dict['contactPoint'] += '<' + pkg_dict['contact_email'] + '>'

    pkg_dict['temporal'] = [
        pkg_dict.get('temporal_from'),
        pkg_dict.get('temporal_to')
    ]

    pkg_dict['accrualPeriodicity'] = pkg_dict.pop('frequency', '')
    pkg_dict['issued'] = pkg_dict.pop('metadata_created')
    pkg_dict['modified'] = pkg_dict.pop('metadata_modified')
    return pkg_dict


def ga_view_count(name):
    return model.Session.query(
        GA_Url.pageviews
    ).filter(GA_Url.period_name == 'All',
             GA_Url.package_id == name).scalar() or 0


class _EEZ:

    def __init__(self, collection):
        self.collection = collection

    def update(self, collection):
        self.collection = collection

    def __iter__(self):
        return iter(self.collection)


eez = _EEZ([])


def store_search_query(search_params):
    logger.debug('after_search {}'.format(search_params))
    try:
        q = search_params['q']
        if not _is_user_text_search(tk.c, q):
            return
        # TODO: If a user performs a text-based search and then
        # continuously refines the result via facets then we end up with
        # many entries for basically the same search, which might screw up
        # our scoring.
        q = _normalize_search_query(q)
        if not q:
            return
        query = SearchQuery.update_or_create(q)
        model.Session.commit()
        return query
    except Exception:
        # Log exception but don't cause search request to fail
        logger.exception('An exception occurred while storing a search query')


def _normalize_search_query(q):
    return ' '.join(q.lower().split()).strip()


def _is_user_text_search(context, query):
    '''
    Decide if a search query is a user-initiated text search.
    '''
    # See https://github.com/ckan/ckanext-searchhistory/issues/1#issue-32079108
    try:
        if (
            context.controller != 'package' or context.action != 'search'
            or (query or '').strip() in (':', '*:*')
        ):
            return False
    except TypeError:
        # Web context not ready. Happens, for example, in paster commands.
        return False
    return True


def is_resource_updatable(id, package_id=None):
    if package_id:
        pkg = model.Package.get(id)
    else:
        pkg = model.Resource.get(id).package

    org = pkg.get_groups('organization')[0]
    org_names = set(
        map(attrgetter('name'), org.get_parent_groups('organization'))
    )
    include_owner = tk.asbool(
        tk.config.get('ckanext.spc.orgs_with_publications_include_root')
    )
    if include_owner:
        org_names.add(org.name)

    restricted_orgs = set(
        tk.aslist(tk.config.get('ckanext.spc.orgs_with_publications'))
    )

    if org_names & restricted_orgs:
        return pkg.private
    return True


def notify_user(user, state, extra_vars):
    """
    Notifies the user about changes in the status of his request
    """
    messages = {
        'approved': 'access/email/spc_request_approved.txt',
        'rejected': 'access/email/spc_request_rejected.txt'
    }
    extra_vars['request_timeout'] = int(
        config.get('spc.access_request.request_timeout_days', 3))
    try:
        mailer.mail_user(
            user,
            "Access request",
            tk.render(messages[state], extra_vars),
        )
    except mailer.MailerException as e:
        logger.error(e)
    except SMTPServerDisconnected as e:
        logger.error(e)


def _get_org_members(org_id):
    data_dict = {
        'id': org_id,
        'include_groups': False,
        'include_tags': False,
        'include_followers': False,
        'include_extras': False
    }
    orgs = logic.get_action('organization_show')(
        {'ignore_auth': True}, data_dict)

    member_ids = (
        member['id'] for member in orgs['users']
        if member['capacity'] in ('admin', 'editor')
    )
    members = (model.User.get(_id) for _id in member_ids)

    return [
        {
            'name': member.name,
            'email': member.email
        } for member in members
    ]


def _send_notifications(admins, extra_vars):
    for admin in admins:
        extra_vars['member'] = admin['name']
        try:
            mailer.mail_recipient(
                admin['name'],
                admin['email'],
                "Access request from - {}".format(extra_vars['user']),
                tk.render('access/email/spc_access_requested.txt', extra_vars),
            )
        except mailer.MailerException as e:
            logger.error(e)
        except SMTPServerDisconnected as e:
            logger.error(e)


def notify_org_members(org_id, extra_vars):
    """
    When user submits data access request notification is sent
    to data custodians (org admins of the owning org) and SPC datahub@spc.int
    """
    members = _get_org_members(org_id)
    datahub_email = config.get('spc.access_request.datahub_email')
    if datahub_email:
        members.append({'name': 'Datahub SPC', 'email': datahub_email})
    _send_notifications(members, extra_vars)


def delete_res_urls_if_restricted(context, data_dict):
    try:
        logic.check_access('restrict_dataset_show', context, data_dict)
        return data_dict
    except logic.NotAuthorized:
        pass

    for resource in data_dict['resources']:
        resource.pop('url')
        resource.pop('url_type')

    return data_dict

def get_package_by_id_or_bust(data_dict):
    pkg_id_or_name = tk.get_or_bust(data_dict, 'id')
    # check if the package with such id exists to use it's ID

    pkg = model.Package.get(pkg_id_or_name)

    if not pkg:
        raise tk.ObjectNotFound()
    return pkg


def params_into_advanced_search(params):
    if not params.get('extras'):
        return params
    try:
        filters = list(zip(*itemgetter('ext_advanced_value', 'ext_advanced_type', 'ext_advanced_operator')(
            tk.request.params.to_dict(False)
        )))
    except KeyError:
        return params
    params.setdefault('fq', '')
    fq = ''

    for value, type, operator in reversed(filters):
        if not value:
            continue
        if type == 'any':
            fragment = f'text:"{value}"'
        elif type == 'title':
            fragment = f'title:"{value}"'
        elif type == 'solr':
            fragment = f'({value})'
        else:
            if re.search(f'\\b{type}\\b', params['fq']):
                continue
            fragment = f'{type}:"{value}"'
        if not fq:
            if operator == 'or':
                fq = 'never:match'
            else:
                fq = '*:*'

        fq = f'{fragment} {operator.upper()} ({fq})'

    params.setdefault('fq_list', []).append(fq)
    return params

def track_resource_download(user, id):
    record = DownloadTracking.download(user, id)
    record.save()
    return record


def refresh_resource_size(id):
    try:
        res = tk.get_action('resource_show')({'ignore_auth': True}, {'id': id})
    except tk.ObjectNotFound:
        logger.error(f'Resource<{id}> was not found')
        return
    entity = model.Resource.get(res['id'])
    if res['url_type'] == 'upload':
        size = _get_local_resource_size(res)
    else:
        size = _get_remote_resource_size(res)
    # Do not change file size to 0 - it may be only temporary unavailable
    if entity.size != size and size:
        entity.size = size
        model.Session.commit()
    return res


def _get_remote_resource_size(res):
    url = res.get('url')
    if not url:
        return 0
    try:
        resp = requests.head(url, timeout=5)
    except requests.exceptions.RequestException:
        logger.exception("Cannot fetch remote metadata for Resource<%s>", res['id'])
        return 0
    try:
        return tk.asint(resp.headers['content-length'])
    except KeyError:
        return 0


def _get_local_resource_size(res):
    uploader = get_resource_uploader(res)
    path = uploader.get_path(res['id'])
    if os.path.isfile(path):
        return os.stat(path).st_size
    return 0
