from flask import jsonify, request
from flask_restful import reqparse, abort, Api, Resource
from data import db_session
from data.posts import Post
from data.users import User
import requests as rq
import json


db_session.global_init("db/blogs.sqlite")


def get_user(token):
    session = db_session.create_session()
    return session.query(User).filter(User.api_token == token).first()


def abort_if_unauthorized(token):
    if not get_user(token):
        abort(401)


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


class UsersResource(Resource):
    def get(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify(user.to_dict(only=('id', 'username', 'about', 'pfp', 'subscribed_by', 'subscribed_to')))

    def post(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        parser.add_argument('action', required=True, type=str)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        if args['action'] == 'subscribe':
            abort_if_user_not_found(user_id)
            session = db_session.create_session()
            target = session.query(User).get(user_id)
            user = session.query(User).filter(User.api_token == args['token']).first()
            if user_id == user.id:
                abort(400, BAD_PARAMETER='user_id')
            if user.id in target.subscribed_by and target.id in user.subscribed_to:
                target.subscribed_by = target.subscribed_by ^ {user.id}
                user.subscribed_to = user.subscribed_to ^ {target.id}
            else:
                target.subscribed_by = target.subscribed_by | {user.id}
                user.subscribed_to = user.subscribed_to | {target.id}
            session.commit()
            return jsonify({'success': 'OK'})
        else:
            abort(400, BAD_PARAMETER='user_id')
