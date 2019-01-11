import logging

import requests

import ckan.lib.helpers as h
import ckan.model as model
from ckan.lib.search import query_for
import ckan.plugins.toolkit as tk

from ckanext.ga_report.ga_model import GA_Url
from ckanext.spc.model import SearchQuery

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
                res['description'] for res in pkg_dict.get('resources', [])
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
            controller='package',
            action='read',
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
        'dataset_read', id=pkg_dict['name'], qualified=True
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
    return model.Session.query(GA_Url.pageviews).filter(
        GA_Url.period_name == 'All', GA_Url.package_id == name
    ).scalar() or 0


class _EEZ:
    def __init__(self, collection):
        self.collection = collection

    def update(self, collection):
        self.collection = collection

    def __iter__(self):
        return iter(self.collection)


eez = _EEZ([])


def store_search_query(search_params):
    import ipdb; ipdb.set_trace()

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
            context.controller != 'package'
            or context.action != 'search'
            or (query or '').strip() in (':', '*:*')
        ):
            return False
    except TypeError:
        # Web context not ready. Happens, for example, in paster commands.
        return False
    return True
