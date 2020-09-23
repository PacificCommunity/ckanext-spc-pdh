import pytest

import ckan.tests.factories as factories

from ckan.logic import ValidationError
from ckan.model.meta import Session

import ckanext.spc.logic.action.create as create

from ckanext.spc.model import AccessRequest


@pytest.mark.usefixtures("clean_db")
class TestCreateAccessRequest:
    def test_create_access_request_by_user(self):
        user = factories.User()
        org_id = factories.Organization()['id']
        pkg_id = factories.Dataset(access='restricted', owner_org=org_id)['id']

        data_dict = {'id': pkg_id, 'reason': 'test', 'user': user['id']}
        res = create.create_access_request(
            {'user': user['name']},
            data_dict
        )

        assert res['id']
        assert res['state'] == 'pending'


    def test_multiple_requests_from_same_user(self):
        user = factories.User()
        org_id = factories.Organization()['id']
        pkg_id = factories.Dataset(access='restricted', owner_org=org_id)['id']

        data_dict = {'id': pkg_id, 'reason': 'test', 'user': user['id']}

        for _ in range(10):
            res = create.create_access_request(
                {'user': user['name']},
                data_dict
            )
        
        assert res['id']
        assert res['state'] == 'pending'

        res_count = Session.query(AccessRequest).count()
        assert res_count == 1

    def test_it_requires_package_id(self):
        user = factories.Sysadmin()
        data_dict = {"user": "username"}

        with pytest.raises(ValidationError):
            create.create_access_request(
                {'user': user['id']},
                data_dict
            )
