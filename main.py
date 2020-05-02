from flask import Flask, url_for, render_template, request
import requests as rq
from data import db_session
from data.users import User
from data.posts import Post
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'howthefuckisthiscodeworking'
CLIENT_ID = 'ed85afc1f5ad48ed97373e897b2d3320'
CLIENT_PASS = 'd6ad865b72d14d16addcf4c38ef840db'
db_session.global_init("db/blogs.sqlite")
session = db_session.create_session()


def authenticate(f):
    def wrapper(*args, **kwargs):
        user_json = get_user(request.cookies.get('SESSION_ID'))
        if user_json:
            user = session.query(User).filter(User.mail == user_json['default_email']).first()
            if not user:
                user = User(username=user_json['login'], mail=user_json['default_email'])
                session.add(user)
                post = Post(content='Registered')
                user.posts.append(post)
                session.commit()
            return f(user_json['login'], *args, **kwargs)
        else:
            return render_template('main.html', not_authorized='1')
    return wrapper


def get_user(token):
    r = rq.get('https://login.yandex.ru/info?format=json&oauth_token=' + str(token))
    if r.text:
        return json.loads(r.text)


def get_username(token):
    r = rq.get('https://login.yandex.ru/info?format=json&oauth_token=' + str(token))
    if r.text:
        return json.loads(r.text)


def get_mail(token):
    r = rq.get('https://login.yandex.ru/info?format=json&oauth_token=' + str(token))
    if r.text:
        return json.loads(r.text)


@app.route('/')
def index():
    return render_template('main.html', content_info='Популярное сегодня')


@app.route('/settings/')
@authenticate
def settings(username):
    return render_template('main.html', content_info=username, content=render_template('settings.html'))


@app.route('/login/')
def login():
    return f'Вы будете перенаправлены в скором времени...<script src={url_for("static", filename="js/login.js")}></script>'


if __name__ == '__main__':
    app.run(port=80, host='127.0.0.1')
