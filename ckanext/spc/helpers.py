import json
import urlparse
import logging
import requests

import iso639

from routes import url_for as _routes_default_url_for

from ckan.common import config

from ckanext.spc.utils import eez
import ckan.lib.helpers as h
from pylons.decorators.cache import beaker_cache

logger = logging.getLogger(__name__)


def get_helpers():
    return dict(
        spc_get_available_languages=spc_get_available_languages,
        url_for_logo=url_for_logo,
        get_conf_site_url=get_conf_site_url,
        get_eez_options=get_eez_options,
        spc_get_footer=spc_get_footer,
        get_footer_css_url=get_footer_css_url
    )


def spc_get_available_languages():
    return filter(
        lambda (n, _): n,
        [(lang['iso639_1'] or lang['iso639_1'], lang['name'])
         for lang in iso639.data]
    )


def url_for_logo(*args, **kw):
    def fix_arg(arg):
        url = urlparse.urlparse(str(arg))
        url_is_relative = (
            url.scheme == '' and url.netloc == ''
            and not url.path.startswith('/')
        )
        if url_is_relative:
            return '/' + url.geturl()
        return url.geturl()

    if args:
        args = (fix_arg(args[0]), ) + args[1:]

    my_url = _routes_default_url_for(*args, **kw)
    return my_url


def get_conf_site_url():
    site_url = config.get('ckan.site_url', None)
    return site_url


def get_eez_options():

    options = sorted([{
        'text': feature['properties']['GeoName'],
        'value': json.dumps(feature['geometry'])
    } for feature in eez],
                     key=lambda o: o['text'])

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


def spc_get_footer():
    drupal_url = config.get('drupal.site_url')
    if drupal_url == None:
        return None
    else:
        get_html = _spc_get_footer_from_drupal(drupal_url)
        return get_html

@beaker_cache(expire=3600)
def _spc_get_footer_from_drupal(drupal_url=None):
    if drupal_url == None or drupal_url == h.full_current_url().split('?')[0][:-1]:
      return None
    r = None
    section_menu = []
    try:
        r = requests.get(drupal_url + '/footer_export', verify=False, timeout=10)
    except requests.exceptions.Timeout:
        log.warning(drupal_url + '/footer_export connection timeout')
    except requests.exceptions.TooManyRedirects:
        log.warning(drupal_url + '/footer_export too many redirects')
    except requests.exceptions.RequestException as e:
        log.error(e.message)

    if r:
      footer = r.json()
    else:
      return None

    if footer and 'main' in footer:
        return footer['main'][0]
    else:
        return None

def get_footer_css_url():
    drupal_url = config.get('drupal.site_url')
    if drupal_url == None:
        return None
    url = drupal_url + '/sites/all/themes/spc/css/footer_css/footer.css'
    return url