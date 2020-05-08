import flask
from flask import url_for, render_template, request, send_from_directory, redirect, abort
from werkzeug.utils import secure_filename
from flask_restful import Api
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

from data import db_session
from data.users import User
from data.posts import Post
import posts_resources
import users_resources
from login_form import LoginForm
from register_form import RegisterForm
from settings_form import SettingsForm

import requests as rq
from PIL import Image
import datetime
import json
import io


app = flask.Flask(__name__)
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'howthefuckisthiscodeworking'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
db_session.global_init("db/blogs.sqlite")
api.add_resource(posts_resources.PostResource, '/api/posts/<int:post_id>')
api.add_resource(posts_resources.PostListResource, '/api/posts')
api.add_resource(users_resources.UsersResource, '/api/users/<int:user_id>')


def replace_symbols(text, replace_map={}):
    for char in replace_map:
        text.replace(char, replace_map[char])
    return text


def get_yandex_user(token):
    r = rq.get('https://login.yandex.ru/info?format=json&oauth_token=' + str(token))
    if r.text:
        return json.loads(r.text)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/login/redirect/')
def login_redirect():
    if 'token' in request.args:
        if current_user.is_authenticated:
            yandex_user = get_yandex_user(request.args['token'])
            if not yandex_user:
                return redirect('/')
            yandex_id = yandex_user['id']
            session = db_session.create_session()
            user = session.query(User).get(current_user.id)
            user.yandex_id = yandex_id
            session.commit()
            return redirect('/settings/')
        else:
            yandex_user = get_yandex_user(request.args['token'])
            if not yandex_user:
                return redirect('/')
            yandex_id = yandex_user['id']
            session = db_session.create_session()
            user = session.query(User).filter(User.yandex_id == yandex_id).first()
            if user:
                login_user(user, remember=True)
                return redirect('/settings/')
            else:
                return redirect('/register/')
    else:
        return f'Вы будете перенаправлены в скором времени...<script src={url_for("static", filename="js/yandex_login.js")}></script>'


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
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
        if wrong:
            return render_template('register.html', form=form)
        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=form.remember_me.data)
        return redirect('/')
    return render_template('register.html', form=form)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', form=form)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        session = db_session.create_session()
        out = ''
        if request.form['offset']:
            posts = session.query(Post).order_by(Post.id.desc()).filter(Post.id < int(request.form['offset']))
        else:
            posts = session.query(Post).order_by(Post.id.desc())
        posts = posts.filter(Post.is_private == False).limit(20)
        for post in posts:
            out += render_template('post.html', post=post, len=len)
        return out


@app.route('/feed/', methods=['GET', 'POST'])
def feed():
    if request.method == 'GET':
        return render_template('feed.html')
    else:
        session = db_session.create_session()
        out = ''
        if request.form['offset']:
            posts = session.query(Post).order_by(Post.id.desc()).filter(Post.id < int(request.form['offset']))
        else:
            posts = session.query(Post).order_by(Post.id.desc())
        if current_user.is_authenticated:
            i = 0
            for post in posts:
                if request.form['show_privates']:
                    if post.author in current_user.subscribed_to or post.user == current_user or post.reply_to.user == current_user:
                        out += render_template('post.html', post=post, len=len)
                        i += 1
                        if i == 20:
                            break
                else:
                    if (post.author in current_user.subscribed_to or post.user == current_user or post.reply_to.user == current_user) and not post.is_private:
                        out += render_template('post.html', post=post, len=len)
                        i += 1
                        if i == 20:
                            break
        return out


@app.route('/blogs/', methods=['GET', 'POST'])
def blogs():
    return redirect('/')


@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        session = db_session.create_session()
        user = session.query(User).get(current_user.id)
        if session.query(User).filter(User.username == form.username.data).first():
            form.username.errors.append('Этот логин уже используется')
            return render_template('settings.html', form=form, current_user=user)
        user.username = form.username.data
        user.about = form.about.data
        if form.pfp.data:
            filename = str(current_user.id) + "_pfp.png"
            img = Image.open(io.BytesIO(form.pfp.data.stream.read()))
            img.thumbnail((128, 128))
            img.save(app.config['UPLOAD_FOLDER'] + filename, "PNG")
            user.pfp = filename
        session.commit()
        return render_template('settings.html', form=form, current_user=user), 201
    return render_template('settings.html', form=form)


@login_required
@app.route('/action/', methods=['POST'])
def action():
    if request.form['action'] == 'like':
        if 'post_id' in request.form:
            session = db_session.create_session()
            post = session.query(Post).get(request.form['post_id'])
            if not post:
                abort(404)
            if current_user.id in post.liked:
                post.liked = post.liked ^ {current_user.id}
            else:
                post.liked = post.liked | {current_user.id}
            session.commit()
    elif request.form['action'] == 'post':
        if 'content' in request.form:
            session = db_session.create_session()
            post = Post(author=current_user.id, content=request.form['content'])
            print(0)
            if 'reply_to' in request.form:
                reply_post = session.query(Post).get(int(request.form['reply_to']))
                if reply_post and (reply_post.is_private or reply_post.reply_to.is_private) and not (reply_post.user == current_user or reply_post.reply_to.user == current_user):
                    post.reply_to_id = session.query(Post).order_by(Post.id.desc()).first().id + 1
                elif reply_post:
                    post.reply_to_id = reply_post.id
                else:
                    post.reply_to_id = session.query(Post).order_by(Post.id.desc()).first().id + 1
            else:
                post.reply_to_id = session.query(Post).order_by(Post.id.desc()).first().id + 1
            session.add(post)
            session.commit()
    return 'OK'


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    app.run(port=80, host='127.0.0.1')
