from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, func

from sqlalchemy.orm import relationship

import ckan.model as model

from ckanext.spc.model import Base


class DownloadTracking(Base):
    __tablename__ = "spc_download_tracking"

    id = Column(Integer, primary_key=True)

    user_id = Column(String, ForeignKey(model.User.id))
    resource_id = Column(String, ForeignKey(model.Resource.id))
    downloaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(model.User)
    resource = relationship(model.Resource, lazy="subquery")

    @classmethod
    def download(cls, user_name_or_id, resource_id):
        obj = cls()
        obj.user_id = model.User.get(user_name_or_id).id
        obj.resource_id = resource_id
        return obj

    def save(self):
        model.Session.add(self)
        model.Session.commit()
        return self

    @classmethod
    def query(cls, id=None, date_range=None, user=None):
        query = (
            model.Session.query(DownloadTracking, model.Resource, model.User)
            .join(
                model.Resource,
                model.Resource.id == DownloadTracking.resource_id,
            )
            .join(model.User, model.User.id == DownloadTracking.user_id)
        ).order_by(DownloadTracking.downloaded_at.desc())
        if id:
            query = query.filter(model.Resource.package_id==id)
        if date_range:
            query = query.filter(cls.downloaded_at.between(*date_range))
        if user:
            query = query.filter(cls.user_id == model.User.get(user).id)
        return query

    @classmethod
    def aggregated_query(cls, date_range=None, user=None):
        downloads = model.Session.query(
            cls.resource_id, func.count(cls.user_id).label("total_downloads")
        ).group_by(cls.resource_id)
        if date_range:
            downloads = downloads.filter(
                cls.downloaded_at.between(*date_range)
            )
        if user:
            downloads = downloads.filter(
                cls.user_id == model.User.get(user).id
            )

        downloads = downloads.subquery()
        query = model.Session.query(
            model.Resource, downloads.c.total_downloads
        ).join(downloads, model.Resource.id == downloads.c.resource_id)
        return query
