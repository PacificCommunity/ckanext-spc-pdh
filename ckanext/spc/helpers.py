import json
import logging
import requests
import iso639
import funcy as F

from urllib.parse import urlparse, urlunparse
from operator import eq, itemgetter
from beaker.cache import CacheManager

import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
from ckan.common import config

from ckanext.spc.utils import eez

logger = logging.getLogger(__name__)
cache = CacheManager()


def get_helpers():
    return dict(
        spc_get_available_languages=spc_get_available_languages,
        get_eez_options=get_eez_options,
        spc_get_footer=spc_get_footer,
        spc_dataset_suggestion_form=spc_dataset_suggestion_form,
        spc_dataset_suggestion_path=spc_dataset_suggestion_path,
        spc_national_map_previews=spc_national_map_previews,
        get_footer_css_url=get_footer_css_url,
        get_dqs_explanation_url=get_dqs_explanation_url,
        get_drupal_user_url=get_drupal_user_url,
        spc_unwrap_list=spc_unwrap_list,
        spc_wrap_list=spc_wrap_list,
        spc_hotjar_enabled=spc_hotjar_enabled,
        spc_link_to_identifier=spc_link_to_identifier,
        spc_has_cesium_view=spc_has_cesium_view,
        spc_get_max_image_size=get_max_image_size,
        spc_get_package_name_by_id=get_package_name_by_id,
        spc_is_restricted=is_restricted,
        spc_is_digital_library_resource=spc_is_digital_library_resource,
        spc_get_package_size=get_package_size,
        spc_get_resource_size=get_resource_size,
        spc_is_preview_maxsize_exceeded=is_preview_maxsize_exceeded,
        spc_get_proxy_res_max_size=get_proxy_res_max_size,
        spc_convert_bytes=convert_bytes,
    )


def countries_list(countries):
    countries_list = []
    try:
        countries_list = json.loads(countries)
    except ValueError:
        countries_list.append(countries)
    return list(map(lambda x: x.upper(), countries_list))


def spc_has_cesium_view(res):
    is_cesium = False
    if res.get('has_views'):
        views = toolkit.get_action('resource_view_list')(
            {'user': toolkit.c.user}, {'id': res['id']})
        is_cesium = any(
            view['view_type'] == 'cesium_view'
            for view in views
        )
    return is_cesium


def spc_dataset_suggestion_form():
    return config.get('spc.dataset_suggestion.form', '/dataset-suggestions/add')


def spc_dataset_suggestion_path():
    return config.get('spc.dataset_suggestion.path', '/dataset-suggestions')


def spc_get_available_languages():
    return filter(
        F.first,
        [(lang['iso639_1'] or lang['iso639_1'], lang['name'])
         for lang in iso639.data]
    )


def get_max_image_size():
    return int(config.get('ckan.max_image_size', 2))


def get_eez_options():

    options = sorted([
        value for value in {
            feature['properties']['Territory1']: {
                'text': feature['properties']['Territory1'],
                'value': json.dumps(feature['geometry'])
            }
            for feature in eez
        }.values()
    ], key=lambda o: o['text'])

    result = []
    for option in options:
        if len(option['value']) / 1024 > 31:
            logger.warning((
                '[{}] has too long coordinates definition '
                'and will be excluded from predefined areas'
            ).format(option['text']))
            continue
        result.append(option)
    # result.append({'text': 'All countries', 'value': 'all'})
    return result


def get_extent_for_country(country):
    spatial = F.first(F.filter(
        F.compose(F.partial(eq, country), itemgetter('text')),
        get_eez_options()
    ))
    return spatial


def spc_get_footer():
    drupal_url = config.get('drupal.site_url')
    if drupal_url:
        get_html = _spc_get_footer_from_drupal(drupal_url)
        return get_html


@cache.cache('footer_from_drupal', expire=3600)
def _spc_get_footer_from_drupal(drupal_url=None):
    if drupal_url is None or drupal_url == h.full_current_url(
    ).split('?')[0][:-1]:
        return None
    r = None
    try:
        r = requests.get(
            drupal_url + '/footer_export', verify=False, timeout=10
        )
    except requests.exceptions.Timeout:
        logger.warning(drupal_url + '/footer_export connection timeout')
    except requests.exceptions.TooManyRedirects:
        logger.warning(drupal_url + '/footer_export too many redirects')
    except requests.exceptions.RequestException as e:
        logger.error(e.message)

    if r:
        footer = r.json()
    else:
        return None

    if footer and 'main' in footer:
        return footer['main'][0]


def get_footer_css_url():
    return '/sites/all/themes/spc/css/footer_css/footer.css'


def get_dqs_explanation_url():
    dqs_explanation_url = config.get('ckan.dqs_explanation_url')
    return dqs_explanation_url


_is_cesium_view = F.compose(
    F.partial(eq, 'cesium_view'),
    itemgetter('view_type')
)


def spc_national_map_previews(pkg):
    return F.filter(F.first, [
        (F.first(F.filter(
            _is_cesium_view,
            toolkit.get_action('resource_view_list')(
                {'user': toolkit.c.user},
                {'id': res['id']}
            )
        )), res) for res in pkg['resources']
    ])


def spc_unwrap_list(value):
    if isinstance(value, list):
        return value[0] if value else {}
    if 0 in value:
        return value[0]
    return value


def spc_wrap_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    if isinstance(value, dict):
        if list(sorted(value.keys())) == list(range(0, len(value))):
            return list(value.values())
    return [value]


def spc_hotjar_enabled():
    enabled = toolkit.asbool(config.get('ckan.spc.hotjar_enabled', False))
    if enabled:
        return True
    return False


def spc_link_to_identifier(id):
    if not id:
        return id
    if id.startswith('doi'):
        return 'http://doi.org/' + id[4:]
    if id.startswith('pmid'):
        return 'https://europepmc.org/abstract/med/' + id[5:]
    return None


def get_drupal_user_url(action, current_url=''):
    current_url_parsed = urlparse(str(current_url))
    drupal_url = config.get('drupal.site_url') or current_url
    url = urlparse(str(drupal_url))
    return_url = f"destination={current_url_parsed.path or ''}"

    if action in ('login', 'register', 'logout'):
        path = f'/user/{action}'
    else:
        path = ''

    return urlunparse((url.scheme, url.netloc, path, '', return_url, ''))


def get_package_name_by_id(package_id):
    from ckan.model import Package
    return Package.get(package_id).title


def is_restricted(package):
    access = package.get('access')

    if 'extras' in package:
        for field in package['extras']:
            if field.get('key') == 'access':
                access = field['value']
                break

    return True if access == 'restricted' else False


def spc_is_digital_library_resource(res):
    lib_host = toolkit.config.get('spc.digital-library.host', 'spc.int')
    return lib_host in res.get('url', '')


def get_resource_size(res: dict) -> str:
    res_bytes: int = res.get('size', 0)
    return convert_bytes(res_bytes)


def get_package_size(pkg: dict) -> str:
    pkg_size: int = 0

    for res in pkg.get('resources', None):
        res_size: int = res.get('size', 0)
        if res_size:
            pkg_size += res_size

    return convert_bytes(pkg_size)


def convert_bytes(B: int) -> str:
    if not B:
        return '0 B'

    B: float = float(B)
    KB: float = float(1024)
    MB: float = float(KB ** 2)  # 1,048,576
    GB: float = float(KB ** 3)  # 1,073,741,824
    TB: float = float(KB ** 4)  # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B, 'B')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B/KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B/MB)
    elif GB <= B < TB:
        return '{0:.2f} GB'.format(B/GB)
    elif TB <= B:
        return '{0:.2f} TB'.format(B/TB)


def is_preview_maxsize_exceeded(res_size: int) -> bool:
    if isinstance(res_size, int):
        return res_size > get_proxy_res_max_size()


def get_proxy_res_max_size() -> int:
    return int(config.get('ckan.resource_proxy.max_file_size', 1024 ** 2))
