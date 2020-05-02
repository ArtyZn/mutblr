import datetime
import sqlalchemy
from sqlalchemy import orm, Column, Integer, String, Boolean, DateTime, PickleType, ForeignKey

from .db_session import SqlAlchemyBase


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
    is_private = Column(Boolean, default=False)

    author = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content = Column(String)
    attachments = Column(PickleType, nullable=True)
    tags = Column(PickleType, nullable=True, index=True)
    liked = Column(PickleType, nullable=True)

    user = orm.relation('User')
