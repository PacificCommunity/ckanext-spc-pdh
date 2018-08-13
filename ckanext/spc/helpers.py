import json
import urlparse

import iso639

from routes import url_for as _routes_default_url_for

from ckan.common import config

from ckanext.spc.utils import eez

def get_helpers():
    return dict(
        spc_get_available_languages=spc_get_available_languages,
        url_for_logo=url_for_logo,
        get_conf_site_url=get_conf_site_url,
        get_eez_options=get_eez_options
    )


def spc_get_available_languages():
    return filter(lambda (n, _): n, [(lang['iso639_1'] or lang['iso639_1'], lang['name'])
            for lang in iso639.data])

def url_for_logo(*args, **kw):
    def fix_arg(arg):
        url = urlparse.urlparse(str(arg))
        url_is_relative = (url.scheme == '' and url.netloc == '' and
                           not url.path.startswith('/'))
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
    return [
        {
            'text': feature['properties']['GeoName'],
            'value': json.dumps(feature['geometry'])
        }
        for feature in eez
    ]
