from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class PostForm(FlaskForm):
    content = TextAreaField('Текст', validators=[DataRequired()])
    tags = StringField('Теги')
    attachments = [FileField('Загрузить файл'), FileField('Загрузить файл'), FileField('Загрузить файл')]
    is_private = BooleanField('Приватный пост')
    submit = SubmitField('Отправить')

    reply_to = StringField('Ответить')