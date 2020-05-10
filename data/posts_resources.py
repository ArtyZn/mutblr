from flask import jsonify
from flask_restful import reqparse, abort, Resource
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


def abort_if_cant_read(post_id, token):
    session = db_session.create_session()
    post = session.query(Post).get(post_id)
    user_id = get_user(token).id
    if post.is_private:
        if post.author != user_id and post.reply_to.author != user_id:
            abort(403, message=f"Can't read post {post_id}")


def abort_if_not_owner(post_id, token):
    session = db_session.create_session()
    post = session.query(Post).get(post_id)
    user_id = get_user(token).id
    if post.author != user_id:
        abort(403, message=f"Not owner of post {post_id}")


def abort_if_post_not_found(post_id):
    session = db_session.create_session()
    post = session.query(Post).get(post_id)
    if not post:
        abort(404, message=f"Post {post_id} not found")


class PostResource(Resource):
    def get(self, post_id):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        args = parser.parse_args()
        token = args['token']
        abort_if_unauthorized(token)
        abort_if_post_not_found(post_id)
        abort_if_cant_read(post_id, token)
        session = db_session.create_session()
        post = session.query(Post).get(post_id)
        resp = post.to_dict(only=('id', 'content', 'user.id', 'user.username', 'is_private'))
        resp['tags'] = post.tags.split()
        resp['likes'] = len(post.liked)
        return jsonify(resp)

    def post(self, post_id):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        parser.add_argument('action', required=True, type=str)
        args = parser.parse_args()
        token = args['token']
        abort_if_unauthorized(token)
        abort_if_post_not_found(post_id)
        abort_if_cant_read(post_id, token)
        user = get_user(token)
        if args['action'] == 'like':
            session = db_session.create_session()
            post = session.query(Post).get(post_id)
            if not post:
                abort(404)
            if user.id in post.liked:
                post.liked = post.liked ^ {user.id}
            else:
                post.liked = post.liked | {user.id}
            session.commit()
            return jsonify({'success': 'OK'})
        else:
            return jsonify({'BAD_PARAMETER': 'action'})

    def delete(self, post_id):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        abort_if_post_not_found(post_id)
        abort_if_not_owner(post_id, args['token'])
        session = db_session.create_session()
        post = session.query(Post).get(post_id)
        post.content = '[DELETED]'
        post.tags = ''
        post.liked = set()
        post.attachments = set()
        session.commit()
        return jsonify({'success': 'OK'})


class PostListResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        parser.add_argument('limit', type=int)
        parser.add_argument('offset', type=int)
        parser.add_argument('author', type=int)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        user = get_user(args['token'])
        session = db_session.create_session()
        limit = int(args['limit']) if args['limit'] else 20
        out = []
        if args['offset']:
            posts = session.query(Post).order_by(Post.id.desc()).filter(Post.id < int(args['offset']))
        else:
            posts = session.query(Post).order_by(Post.id.desc())
        for post in posts:
            if (not post.is_private or post.user == user or post.reply_to.user == user) and (not args['author'] or post.author == int(args['author'])):
                resp = post.to_dict(only=('id', 'content', 'user.id', 'user.username', 'is_private'))
                resp['tags'] = post.tags.split()
                resp['likes'] = len(post.liked)
                out += [resp]
                if len(out) == limit:
                    break
        return jsonify(out)

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        parser.add_argument('content', required=True, type=str)
        parser.add_argument('tags', required=False, type=str)
        parser.add_argument('is_private', required=False, type=bool)
        parser.add_argument('reply_to', required=False, type=int)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        session = db_session.create_session()
        post = Post(content=args['content'], author=get_user(args['token']).id)
        if args['tags'] is not None:
            post.tags = ' ' + args['tags']
        if args['is_private'] is not None:
            post.is_private = args['is_private']
        if args['reply_to'] is not None:
            abort_if_post_not_found(args['reply_to'])
            abort_if_cant_read(args['reply_to'], args['token'])
            reply_post = session.query(Post).get(args['reply_to'])
            if reply_post:
                post.reply_to_id = args['reply_to']
                if reply_post.is_private:
                    post.is_private = True
        else:
            lpost = session.query(Post).order_by(Post.id.desc()).first()
            if lpost:
                post.reply_to_id = lpost.id + 1
            else:
                post.reply_to_id = 1
        session.add(post)
        session.commit()
        return jsonify({'post_id': post.id})
