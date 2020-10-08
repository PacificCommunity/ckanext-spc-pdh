import pytest

import ckan.tests.factories as factories
import ckan.lib.helpers as helpers
import ckan.logic as logic


@pytest.mark.usefixtures("clean_db", "with_request_context")
class TestResourceRead(object):
    def test_resource_read_anon_user(self, app):
        dataset = factories.Dataset(access='restricted')
        resource = factories.Resource(package_id=dataset["id"])

        url = helpers.url_for(
            "{}_resource.read".format(dataset["type"]),
            id=dataset["id"], resource_id=resource["id"]
        )

        resp = app.get(url, status=200)
        assert resource['url'] not in resp

    def test_resource_read_sysadmin(self, app):
        sysadmin = factories.Sysadmin()
        env = {"REMOTE_USER": sysadmin["name"]}
        dataset = factories.Dataset(access='restricted')
        resource = factories.Resource(package_id=dataset["id"])

        url = helpers.url_for(
            "{}_resource.read".format(dataset["type"]),
            id=dataset["id"], resource_id=resource["id"]
        )

        resp = app.get(url, status=200, extra_environ=env)
        assert resource['url'] in resp

    def test_resource_read_by_editor(self, app):
        user = factories.User()
        env = {"REMOTE_USER": user["name"]}
        org = factories.Organization(
            users=[{"name": user["name"], "capacity": "editor"}]
        )
        dataset = factories.Dataset(access="restricted", owner_org=org['id'])
        resource = factories.Resource(package_id=dataset["id"])

        url = helpers.url_for(
            "{}_resource.read".format(dataset["type"]),
            id=dataset["id"], resource_id=resource["id"]
        )

        resp = app.get(url, status=200, extra_environ=env)
        assert resource['url'] in resp

    def test_resource_read_with_access(self, app):
        user = factories.User()
        env = {"REMOTE_USER": user["name"]}
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org['id'], access='restricted')
        resource = factories.Resource(package_id=dataset["id"])

        data_dict = {
            'id': dataset['id'],
            'reason': 'test',
            'user': user['name']
        }

        logic.get_action('create_access_request')(
            {'user': user['name']},
            data_dict
        )

        logic.get_action('approve_access')(
            {'ignore_auth': True},
            data_dict
        )
        url = helpers.url_for(
            "{}_resource.read".format(dataset["type"]),
            id=dataset["id"], resource_id=resource["id"]
        )

        resp = app.get(url, status=200, extra_environ=env)
        assert resource['url'] in resp
