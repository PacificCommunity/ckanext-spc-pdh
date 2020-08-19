import pytest
import uuid

from ckanext.spc.model import AccessRequest
from ckanext.spc.tests.factories import create_request


def _generate_uuid(username, package_id):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, (username + package_id)))


@pytest.mark.usefixtures("clean_db")
def test_create_or_get_request():
    req1 = create_request()
    assert req1.state == "pending"
    assert req1.id == _generate_uuid('user', 'package')

    req2 = create_request()

    assert req1.id == req2.id


@pytest.mark.usefixtures("clean_db")
def test_create_with_custom_state():
    req = create_request(state='approved')
    assert req.state == "approved"


@pytest.mark.usefixtures("clean_db")
def test_approve_request():
    req = create_request()
    assert req.state == "pending"

    AccessRequest.set_access_request_state(
        user_id='user', package_id='package', state='approved')
    assert req.state == 'approved'


@pytest.mark.usefixtures("clean_db")
def test_approve_request_by_request_id():
    req = create_request()
    assert req.state == "pending"

    AccessRequest.set_access_request_state(
        user_id='user',
        package_id='package',
        state='approved',
        request_id=req.id
    )
    assert req.state == 'approved'


def test_reject_request():
    req = create_request(state='approved')

    assert req.state == "approved"

    AccessRequest.set_access_request_state(
        user_id='user',
        package_id='package',
        state='rejected'
    )
    assert req.state == 'rejected'


@pytest.mark.usefixtures("clean_db")
def test_reject_request_by_request_id():
    req = create_request(state='approved')
    assert req.state == "approved"

    AccessRequest.set_access_request_state(
        user_id='user',
        package_id='package',
        state='rejected',
        request_id=req.id
    )
    assert req.state == 'rejected'


@pytest.mark.usefixtures("clean_db")
def test_approve_not_existing_request():
    req = AccessRequest.set_access_request_state(
        user_id='user',
        package_id='package',
        state='rejected'
    )
    assert not req


@pytest.mark.usefixtures("clean_db")
def test_get_org_pending_requests():
    create_request(user_id='user1', package_id='package1')
    create_request(user_id='user2', package_id='package2')
    create_request(user_id='user3', package_id='package3', state='approved')

    reqs = AccessRequest.get_access_requests_for_org(
        id='org-name', state='pending')

    assert reqs.count() == 2


@pytest.mark.usefixtures("clean_db")
def test_get_package_approved_requests():
    create_request(user_id='user1')
    create_request(user_id='user2', state='approved')
    create_request(user_id='user3', state='approved')
    reqs = AccessRequest.get_access_requests_for_pkg(
        id='package', state='approved')

    assert reqs.count() == 2
