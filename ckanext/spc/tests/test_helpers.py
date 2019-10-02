"""Tests for plugin.py."""
import os
import nose.tools as nt

import ckanext.spc.helpers as helpers
from ckanext.spc.command import SPCCommand


def test_spc_get_available_languages():
    languages = helpers.spc_get_available_languages()
    nt.ok_(all(n and v for n, v in languages))


ROOT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '../../..')
)


class _CLI:

    def __init__(self):
        self.cmd = SPCCommand('lego')

    def run(self, *args):
        return self.cmd.run(list(args) + ['-c', ROOT_DIR + '/test.ini'])


cli = _CLI()
