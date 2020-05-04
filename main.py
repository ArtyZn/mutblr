import flask
from flask import url_for, render_template, request, send_from_directory, redirect
from flask_restful import Api
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

from data import db_session
from data.users import User
from data.posts import Post
import posts_resources
import users_resources
from login_form import LoginForm
from register_form import RegisterForm

import requests as rq
import datetime
import json


app = flask.Flask(__name__)
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'howthefuckisthiscodeworking'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
db_session.global_init("db/blogs.sqlite")
api.add_resource(posts_resources.PostResource, '/api/posts/<int:post_id>')
api.add_resource(posts_resources.PostListResource, '/api/posts')
api.add_resource(users_resources.UsersResource, '/api/users/<int:user_id>')


def get_yandex_user(token):
    r = rq.get('https://login.yandex.ru/info?format=json&oauth_token=' + str(token))
    if r.text:
        return json.loads(r.text)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings/', methods=['GET', 'POST'])
def settings():

    return render_template('settings.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', form=form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        wrong = False
        if session.query(User).filter(User.email == form.email.data).first():
            form.email.errors.append("Этот почтовый адрес уже используется")
            wrong = True
        if session.query(User).filter(User.username == form.username.data).first():
            form.username.errors.append("Этот логин уже используется")
            wrong = True
        if form.password.data != form.password_repeat.data:
            form.password_repeat.errors.append("Пароли не совпадают")
            wrong = True
        if len(form.password.data) < 8:
            form.password.errors.append("Пароль должен быть длиннее 7 символов")
            wrong = True
        if wrong:
            return render_template('register.html', form=form)
        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=form.remember_me.data)
        return redirect('/')
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login/redirect/')
def login_redirect():
    if 'token' in request.data:
        flask.session['token'] = request.data['token']
    else:
        return f'Вы будете перенаправлены в скором времени...<script src={url_for("static", filename="js/login.js")}></script>'


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(port=80, host='127.0.0.1')