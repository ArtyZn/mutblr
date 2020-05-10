import flask
from flask import url_for, render_template, request, send_from_directory, redirect, abort
from flask_restful import Api
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

from data import db_session
from data.users import User
from data.posts import Post
from data import posts_resources
from data import users_resources
from data.login_form import LoginForm
from data.register_form import RegisterForm
from data.settings_form import SettingsForm
from data.post_form import PostForm

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
            if session.query(User).filter(User.yandex_id == yandex_id).first():
                session.query(User).filter(User.yandex_id == yandex_id).first().yandex_id = None
                session.commit()
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
                    if (post.user == current_user or post.reply_to.user == current_user) or (post.author in current_user.subscribed_to and not post.is_private):
                        out += render_template('post.html', post=post, len=len)
                        i += 1
                        if i == 20:
                            break
                else:
                    if ((post.user == current_user or post.reply_to.user == current_user) or (post.author in current_user.subscribed_to)) and not post.is_private:
                        out += render_template('post.html', post=post, len=len)
                        i += 1
                        if i == 20:
                            break
        return out


@app.route('/blogs/', methods=['GET', 'POST'])
def blogs():
    if request.method == 'GET':
        return render_template('blogs.html')
    else:
        session = db_session.create_session()
        out = ''
        offset = request.form['offset'] if request.form['offset'] else 0
        if current_user.is_authenticated:
            subscribed_to = current_user.subscribed_to
            i = 0
            for user_id in subscribed_to:
                out += render_template('blog.html', user=session.query(User).get(user_id))
                i += 1
                if i == 20:
                    return out
        return out


@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        session = db_session.create_session()
        user = session.query(User).get(current_user.id)
        if form.username.data != current_user.username and session.query(User).filter(User.username == form.username.data).first():
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


@app.route('/user/<int:user_id>', methods=["GET", "POST"])
def user(user_id):
    if request.method == 'GET':
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        if user:
            return render_template('user.html', user=user)
        else:
            abort(404)
    else:
        session = db_session.create_session()
        out = ''
        if request.form['offset']:
            posts = session.query(Post).order_by(Post.id.desc()).filter(Post.author == user_id, Post.id < int(request.form['offset']))
        else:
            posts = session.query(Post).order_by(Post.id.desc()).filter(Post.author == user_id)
        if current_user.is_authenticated:
            i = 0
            for post in posts:
                if (post.user == current_user or post.reply_to.user == current_user) or not post.is_private:
                    out += render_template('post.html', post=post, len=len)
                    i += 1
                    if i == 20:
                        break
        return out


@login_required
@app.route('/user/<int:user_id>/subscribe', methods=["POST"])
def user_subscribe(user_id):
    session = db_session.create_session()
    target = session.query(User).get(user_id)
    user = session.query(User).get(current_user.id)
    if target:
        if user.id in target.subscribed_by and target.id in user.subscribed_to:
            target.subscribed_by = target.subscribed_by ^ {user.id}
            user.subscribed_to = user.subscribed_to ^ {target.id}
        else:
            target.subscribed_by = target.subscribed_by | {user.id}
            user.subscribed_to = user.subscribed_to | {target.id}
        session.commit()


@login_required
@app.route('/post/', methods=["GET", "POST"])
def send_post():
    form = PostForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        post = Post(author=current_user.id, content=form.content.data, tags=' ' + form.tags.data if form.tags.data else '', is_private=form.is_private.data)
        if form.reply_to.data:
            reply_post = session.query(Post).get(int(form.reply_to.data))
            if reply_post and reply_post.is_private and not (reply_post.user == current_user or reply_post.reply_to.user == current_user):
                lpost = session.query(Post).order_by(Post.id.desc()).first()
                if lpost:
                    post.reply_to_id = lpost.id + 1
                else:
                    post.reply_to_id = 1
            elif reply_post:
                post.reply_to_id = reply_post.id
                if reply_post.is_private:
                    post.is_private = True
            else:
                lpost = session.query(Post).order_by(Post.id.desc()).first()
                if lpost:
                    post.reply_to_id = lpost.id + 1
                else:
                    post.reply_to_id = 1
        else:
            lpost = session.query(Post).order_by(Post.id.desc()).first()
            if lpost:
                post.reply_to_id = lpost.id + 1
            else:
                post.reply_to_id = 1

        session.add(post)
        session.commit()
    return render_template('postform.html', form=form)


@app.route('/post/<int:post_id>')
def post(post_id):
    session = db_session.create_session()
    post = session.query(Post).get(post_id)
    if not post:
        abort(404)
    posts = []
    if post.is_private and post.author != current_user.id and post.reply_to.author != current_user.id:
        abort(403)
    while post.id != post.reply_to_id:
        posts.append(post)
        post = post.reply_to
    posts.append(post.reply_to)
    return render_template('full_thread.html', posts=posts, len=len)


@login_required
@app.route('/post/<int:post_id>/delete', methods=['POST'])
def post_delete(post_id):
    session = db_session.create_session()
    post = session.query(Post).get(post_id)
    if current_user.id == post.author:
        post.content = '[DELETED]'
        post.tags = ''
        post.liked = set()
        post.attachments = set()
        session.commit()
    else:
        abort(403)
    return ''


@login_required
@app.route('/post/<int:post_id>/like', methods=['POST'])
def post_like(post_id):
    session = db_session.create_session()
    post = session.query(Post).get(post_id)
    if not post:
        abort(404)
    if current_user.id in post.liked:
        post.liked = post.liked ^ {current_user.id}
    else:
        post.liked = post.liked | {current_user.id}
    session.commit()


@app.route('/search/', methods=["POST"])
def search_empty():
    return "No results!"


@app.route('/search/<string:keyword>', methods=["POST"])
def search(keyword):
    session = db_session.create_session()
    users = session.query(User).filter(User.username.like(f'%{keyword}%')).limit(3)
    posts = session.query(Post).filter(Post.tags.like(f'% {keyword}%'), Post.is_private != True).limit(3)
    return render_template('searchpanel.html', users=users, posts=posts)


@login_required
@app.route('/action/', methods=['POST'])
def action():
    if request.form['action'] == 'getusercard':
        pass
    elif request.form['action'] == 'getcuruserid':
        return str(current_user.id)
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
