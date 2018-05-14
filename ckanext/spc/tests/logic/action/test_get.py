import nose.tools as nt
import ckanext.spc.logic.action.get as get
import ckan.plugins.toolkit as tk


def test_spc_dcat_show_id_required():
    nt.assert_raises(tk.ValidationError, get.spc_dcat_show, None, {})
