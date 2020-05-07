from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class SettingsForm(FlaskForm):
    username = StringField()
    about = TextAreaField()
    submit = SubmitField()
