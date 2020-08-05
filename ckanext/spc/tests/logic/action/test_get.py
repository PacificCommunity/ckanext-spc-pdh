import pytest
import ckanext.spc.logic.action.get as get
import ckan.plugins.toolkit as tk


def test_spc_dcat_show_id_required():
    with pytest.raises(tk.ValidationError):
        get.spc_dcat_show(None, {})
