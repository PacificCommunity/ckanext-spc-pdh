import iso639


def get_helpers():
    return dict(spc_get_available_languages=spc_get_available_languages)


def spc_get_available_languages():
    return filter(lambda (n, _): n, [(lang['iso639_1'] or lang['iso639_1'], lang['name'])
            for lang in iso639.data])
