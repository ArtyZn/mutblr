from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class SettingsForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4)])
    about = TextAreaField('О себе')
    pfp = FileField('Загрузка аватара')
    submit = SubmitField('Сохранить изменения')
