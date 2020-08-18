import pytest
import ckanext.spc.logic.action.get as get
import ckan.plugins.toolkit as tk
import ckan.logic as logic

from ckanext.spc.model import AccessRequest
from ckanext.spc.tests.factories import create_request

import ckan.tests.factories as factories


def test_spc_dcat_show_id_required():
    with pytest.raises(tk.ValidationError):
        get.spc_dcat_show(None, {})


@pytest.mark.usefixtures("clean_db",)
class TestGetAccessRequest:
    def test_get_access_request_by_sysadmin(self):
        sysadmin = factories.Sysadmin()
        user = factories.User()
        pkg = factories.Dataset()

        create_request(user_id=user['name'], package_id=pkg['id'])

        req = get.get_access_request(
            {'user': sysadmin['name']},
            {'id': pkg['id'], 'user': user['name']}
        )

        assert req

    def test_get_access_request_by_user(self):
        user = factories.User()
        pkg = factories.Dataset()

        create_request(user_id=user['name'], package_id=pkg['id'])

        req = get.get_access_request(
            {'user': user['name']},
            {'id': pkg['id'], 'user': user['name']}
        )

        assert req

    def test_get_access_request_by_anon(self):
        pkg = factories.Dataset()
        user = factories.User()
        create_request(package_id=pkg['id'], user_id=user['id'])

        with pytest.raises(logic.NotAuthorized):
            get.get_access_request(
                {},
                {'id': pkg['id'], 'user': user['name']}
            )

    def test_get_access_request_id_required(self):
        user = factories.Sysadmin()
        pkg = factories.Dataset()
        create_request(user_id=user['name'], package_id=pkg['id'])

        with pytest.raises(logic.ValidationError):
            get.get_access_request({'user': user['name']}, {})

    def test_get_access_requests_list_for_pkg(self):
        user1 = factories.User(name='user1')
        user2 = factories.User(name='user2')
        sysadmin = factories.Sysadmin()

        pkg = factories.Dataset()

        create_request(user_id=user1['name'], package_id=pkg['id'])
        create_request(user_id=user2['name'], package_id=pkg['id'])

        reqs = get.get_access_requests_for_pkg(
            {'user': sysadmin['name']}, {'id': pkg['id']})

        assert len(reqs) == 2

    def test_get_access_requests_list_for_pkg_by_anon(self):
        pkg = factories.Dataset()

        with pytest.raises(logic.NotAuthorized):
            get.get_access_requests_for_pkg({}, {'id': pkg['id']})

    def test_get_access_requests_list_for_pkg_by_user(self):
        pkg = factories.Dataset()
        user = factories.User()

        with pytest.raises(logic.NotAuthorized):
            get.get_access_requests_for_pkg(
                {'user': user['id']}, {'id': pkg['id']})

    def test_get_access_requests_list_for_org_by_member(self):
        user = factories.User()
        org = factories.Organization(
            users=[{"name": user["name"], "capacity": "editor"}]
        )
        dataset = factories.Dataset(owner_org=org['id'])

        create_request(package_id=dataset['id'], org_id=org['id'])

        res = get.get_access_requests_for_org(
                {'user': user['name']}, {'id': org['id']})
        
        assert len(res) == 1