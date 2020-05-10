import datetime
from sqlalchemy import orm, Column, Integer, String, Boolean, DateTime, PickleType, ForeignKey
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Post(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
    is_private = Column(Boolean, default=False)
    reply_to_id = Column(Integer, ForeignKey('posts.id'))

    author = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content = Column(String)
    attachments = Column(PickleType, nullable=True, default=[])
    tags = Column(String, nullable=True, default='')
    liked = Column(PickleType, nullable=True, default=set())

    user = orm.relation('User')
    reply_to = orm.relationship('Post', remote_side=[id])
