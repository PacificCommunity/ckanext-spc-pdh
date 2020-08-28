import uuid

from datetime import datetime as dt
from sqlalchemy import Column, String, DateTime

import ckan.model.meta as meta
from ckan.plugins.toolkit import ObjectNotFound

from ckanext.spc.model import Base


class AccessRequest(Base):
    """
    this model represents the access_request table

    if the dataset has access:restricted attribute
    user able to request an access to get it's data without restrictions
    """
    __tablename__ = "spc_access_request"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    package_id = Column(String)
    org_id = Column(String)
    state = Column(String)
    reason = Column(String)
    data_modified = Column(DateTime, default=dt.utcnow())

    def as_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'package_id': self.package_id,
            'org_id': self.org_id,
            'state': self.state,
            'reason': self.reason,
            'data_modified': self.data_modified.isoformat()
        }

    @property
    def is_pending(self):
        return True if self.state == 'pending' else False

    @staticmethod
    def _generate_uuid(user_id, package_id):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, (user_id + package_id)))

    @classmethod
    def check_access_to_dataset(cls, user_id, package_id):
        """
        checks if the user has an access to the dataset
        based on user_id and package_id

        returns boolean value
        """

        req = meta.Session.query(cls).filter_by(
            user_id=user_id,
            package_id=package_id,
            state='approved'
        ).count()

        return True if req else False

    @classmethod
    def set_access_request_state(cls, user_id, package_id, state, request_id=None, reason=None):
        """
        tries to set a specified state to an access_request entity
        if there is no such entity - raises ObjectNotFound
        """
        if not request_id:
            request_id = cls._generate_uuid(user_id, package_id)
        req = meta.Session.query(cls).get(request_id)
        if not req:
            return
        req.state = state
        req.data_modified = dt.utcnow()

        if reason:
            req.reason = reason

        meta.Session.commit()
        return req

    @classmethod
    def get(cls, user_id, package_id):
        _id = cls._generate_uuid(user_id, package_id)
        return meta.Session.query(cls).get(_id)

    @classmethod
    def get_by_id(cls, request_id):
        return meta.Session.query(cls).get(request_id)

    @classmethod
    def create(cls, user_id, package_id, reason, org_id, state='pending'):
        _id = cls._generate_uuid(user_id, package_id)
        req = AccessRequest(
            id=_id,
            user_id=user_id,
            package_id=package_id,
            org_id=org_id,
            state=state,
            reason=reason
        )
        meta.Session.add(req)
        meta.Session.commit()

        return req

    @classmethod
    def create_or_get_request(cls, user_id, package_id, reason, org_id, state='pending'):
        """
        creates a new access requests if requests with ID doesn't exists
        otherwise returns the existed one

        ID build up with uuid5(user_id + package_id)
        """

        req = AccessRequest.get(user_id, package_id)

        # if we found an access_request then return it
        if req:
            return req

        # otherwise - create a new one with default state 'pending'
        req = AccessRequest.create(user_id, package_id, reason, org_id, state)

        return req

    @classmethod
    def get_access_requests_for_org(cls, id, state=None):
        if state:
            return meta.Session.query(cls).filter_by(
                org_id=id, state=state)
        return meta.Session.query(cls).filter_by(org_id=id)

    @classmethod
    def get_access_requests_for_pkg(cls, id, state=None):
        if state:
            return meta.Session.query(cls).filter_by(
                package_id=id, state=state)
        return meta.Session.query(cls).filter_by(package_id=id)
