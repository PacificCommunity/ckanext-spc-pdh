import iso639
import urlparse
from routes import url_for as _routes_default_url_for

def get_helpers():
    return dict(spc_get_available_languages=spc_get_available_languages,
                url_for_logo=url_for_logo)


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
