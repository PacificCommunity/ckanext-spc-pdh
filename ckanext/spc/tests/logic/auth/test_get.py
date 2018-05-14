import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.helpers as helpers
import nose.tools as nt


def test_spc_dcat_show():
    nt.ok_(
        helpers.call_auth(
            'spc_dcat_show', {
                'model': model,
                'user': 'test.ckan.net'
            }
        )
    )
    nt.assert_raises(
        tk.NotAuthorized, helpers.call_auth, 'spc_dcat_show', {
            'model': model,
            'user': ''
        }
    )
