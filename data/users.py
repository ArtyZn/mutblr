import datetime
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, index=True)
    username = sqlalchemy.Column(sqlalchemy.String, unique=True, index=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, index=True)
    password_hash = sqlalchemy.Column(sqlalchemy.String)
    api_token = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)

    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    pfp = sqlalchemy.Column(sqlalchemy.String, default='default_pfp.png')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    subscribed_by = sqlalchemy.Column(sqlalchemy.PickleType, nullable=True, default=set())
    subscribed_to = sqlalchemy.Column(sqlalchemy.PickleType, nullable=True, default=set())

    posts = orm.relation("Post", back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
