from flask import Flask
from data import db_session
from data.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def main():
    global db_session
    db_session.global_init("db/blogs.sqlite")
    user = User()
    user.username = "admin"
    user.about = "he admins"
    session = db_session.create_session()
    session.add(user)
    session.commit()
    app.run()


if __name__ == '__main__':
    main()