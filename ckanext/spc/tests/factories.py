from ckanext.spc.model import AccessRequest


def create_request(user_id='user',
                    package_id='package',
                    org_id='org-name',
                    state='pending',
                    reason='for fun'):
    return AccessRequest.create_or_get_request(
        user_id=user_id, package_id=package_id, org_id=org_id,
        state=state, reason=reason)