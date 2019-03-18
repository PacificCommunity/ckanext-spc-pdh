from sqlalchemy import Column, UnicodeText, Integer

from ckanext.spc.model import Base
import ckan.model.meta as meta


class SearchQuery(Base):
    __tablename__ = 'spc_search_queries'

    query = Column(UnicodeText, primary_key=True)
    count = Column(Integer, default=0)

    @classmethod
    def update_or_create(cls, query):
        existing = meta.Session.query(cls).filter_by(query=query).first()
        if existing is None:
            existing = SearchQuery()
            existing.query, existing.count = query, 0
            meta.Session.add(existing)

        existing.count += 1
        return existing
