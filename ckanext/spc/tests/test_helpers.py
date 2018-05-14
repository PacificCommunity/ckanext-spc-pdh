"""Tests for plugin.py."""
import nose.tools as nt

import ckanext.spc.helpers as helpers


def test_spc_get_available_languages():
    languages = helpers.spc_get_available_languages()
    nt.ok_(all(n and v for n, v in languages))
