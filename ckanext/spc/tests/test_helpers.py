import ckanext.spc.helpers as helpers


def test_spc_get_available_languages():
    languages = helpers.spc_get_available_languages()
    assert all(n and v for n, v in languages)
