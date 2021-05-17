from sqlalchemy import Column, String, Integer

from ckanext.spc.model import Base
import ckan.model.meta as meta


class DrupalUser(Base):
    __tablename__ = "spc_drupal_user"

    ckan_user = Column(String, primary_key=True)
    drupal_user = Column(Integer)

    @classmethod
    def get_or_add(cls, ckan_user, drupal_user):
        if not ckan_user:
            user = (
                meta.Session.query(cls)
                .filter_by(drupal_user=drupal_user)
                .one_or_none()
            )
            return user

        user = (
            meta.Session.query(cls)
            .filter_by(ckan_user=ckan_user)
            .one_or_none()
        )
        if user is None:
            user = DrupalUser()
            user.ckan_user, user.drupal_user = ckan_user, drupal_user
            meta.Session.add(user)

        return user
