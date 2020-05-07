from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class RegisterForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    password_repeat = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    username = StringField('Логин', validators=[DataRequired(), Length(min=4)])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегистрироваться')
