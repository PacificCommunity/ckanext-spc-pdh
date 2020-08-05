import pytest
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.helpers as helpers


def test_spc_dcat_show():

    assert helpers.call_auth(
        "spc_dcat_show", {"model": model, "user": "test.ckan.net"}
    )
    with pytest.raises(tk.NotAuthorized):
        helpers.call_auth(
            "spc_dcat_show", {"model": model, "user": ""},
        )
