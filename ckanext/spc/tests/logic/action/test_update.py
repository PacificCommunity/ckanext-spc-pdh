import pytest

import ckan.tests.factories as factories

import ckanext.spc.logic.action.create as create
import ckanext.spc.logic.action.update as update


@pytest.mark.usefixtures("clean_db")
class TestUpdateAccessRequest:
    def test_change_access_request_state(self):
        user = factories.User()
        context = {'user': user['name']}

        org_id = factories.Organization()['id']
        pkg_id = factories.Dataset(access='restricted', owner_org=org_id)['id']
        data_dict = {'id': pkg_id, 'reason': 'test', 'user': user['id']}

        res = create.create_access_request(context, data_dict)

        assert res['id']
        assert res['state'] == 'pending'

        context = {'ignore_auth': True}

        res = update.reject_access(context, data_dict)

        assert res['state'] == 'rejected'

        res = update.update_access(context, data_dict)

        assert res['state'] == 'pending'

        res = update.approve_access(context, data_dict)

        assert res['state'] == 'approved'
