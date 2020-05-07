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
    if token == "guest":
        if post.is_private:
            abort(403, message=f"Can't read post {post_id}")
        else:
            return
    user_id = get_user(token).id
    if post.is_private:
        if post.author == user_id:
            return
        if post.reply_to:
            post = session.query(Post).get(post.reply_to)
            if post.author == user_id:
                return
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
        abort_if_unauthorized(args['token'])
        abort_if_post_not_found(post_id)
        abort_if_cant_read(post_id, args['token'])
        session = db_session.create_session()
        post = session.query(Post).get(post_id)
        return jsonify(post.to_dict(only=('id', 'content', 'author', 'user.username', 'user.pfp', 'is_private', 'attachments', 'tags', 'liked')))

    def post(self, post_id):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        parser.add_argument('action', required=True, type=str)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        abort_if_post_not_found(post_id)
        session = db_session.create_session()
        if args['action'] == 'like':
            post = session.query(Post).get(post_id)
            post.liked = post.liked | {get_user(args['token']).id}
            session.commit()
            return jsonify({'success': 'OK'})
        elif args['action'] == 'dislike':
            post = session.query(Post).get(post_id)
            post.liked = post.liked ^ {get_user(args['token']).id}
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
        session.delete(post)
        session.commit()
        return jsonify({'success': 'OK'})


class PostListResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        parser.add_argument('feed', type=bool)
        parser.add_argument('limit', type=int)
        parser.add_argument('offset', type=int)
        parser.add_argument('author', type=int)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        session = db_session.create_session()
        limit = 20
        offset = 0
        posts = []
        if args['limit'] and 0 < args['limit'] < 20:
            limit = args['limit']
        if args['offset'] and 0 < args['offset']:
            offset = args['offset']
        if args['feed']:
            user_id = get_user(args['token']).id
            if args['author']:
                for post in session.query(User).get(args['author']).posts:
                    if not post.is_private or post.author == user_id or (post.reply_to and session.query(Post).get(post.reply_to).author == user_id):
                        posts.append(post)
                        if len(posts) == offset + limit:
                            break
            else:
                for post in session.query(Post):
                    if not post.is_private or post.author == user_id or (post.reply_to and session.query(Post).get(post.reply_to).author == user_id):
                        posts.append(post)
                        if len(posts) == offset + limit:
                            break
        else:
            if args['author']:
                for post in session.query(User).get(args['author']).posts:
                    if not post.is_private:
                        posts.append(post)
                        if len(posts) == offset + limit:
                            break
            else:
                for post in session.query(Post):
                    if not post.is_private:
                        posts.append(post)
                        if len(posts) == offset + limit:
                            break
        posts = posts[offset:offset + limit]
        return jsonify({'posts': [item.to_dict(only=('id', 'content', 'author', 'user.username', 'user.pfp', 'is_private', 'attachments', 'tags', 'liked'))
                                  for item in posts]})

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('token', required=True, type=str)
        parser.add_argument('content', required=True, type=str)
        parser.add_argument('attachments', required=False, type=list)
        parser.add_argument('tags', required=False, type=set)
        parser.add_argument('is_private', required=False, type=bool)
        parser.add_argument('reply_to', required=False, type=int)
        args = parser.parse_args()
        abort_if_unauthorized(args['token'])
        session = db_session.create_session()
        post = Post(content=args['content'], author=get_user(args['token']).id)
        if args['attachments'] is not None:
            post.attachments = args['attachments']
        if args['tags'] is not None:
            post.tags = args['tags']
        if args['is_private'] is not None:
            post.is_private = args['is_private']
        if args['reply_to'] is not None:
            reply_post = session.query(Post).get(args['reply_to'])
            if reply_post:
                post.reply_to = args['reply_to']
                if reply_post.is_private:
                    post.is_private = True
        session.add(post)
        session.commit()
        return jsonify({'success': 'OK'})
