from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import EqualTo, InputRequired, Length, ValidationError

from app.models import UserM
from app.roles import ROLE_CHOICES


class LoginForm(FlaskForm):
    username = StringField('Username', [InputRequired(message='Username is required.')])
    password = PasswordField('Password', [InputRequired(message='Password is required.')])
    submit = SubmitField('Sign In')


class SetupForm(FlaskForm):
    username = StringField('Username', [InputRequired(), Length(max=128)])
    password = PasswordField('Password', [InputRequired()])
    password_2 = PasswordField('Repeat Password', [
        InputRequired(),
        EqualTo('password', message='Passwords must match.'),
    ])
    submit = SubmitField('Create admin account')


class UserForm(FlaskForm):
    id = HiddenField('id', [InputRequired()])
    username = StringField('Username', [InputRequired(), Length(max=128)])
    password = PasswordField('Password')
    password_2 = PasswordField('Repeat Password', [EqualTo('password', message='Passwords must match.')])
    role = SelectField('Role', [InputRequired()], choices=ROLE_CHOICES, coerce=str)
    status = SelectField('Status', [InputRequired()],
                         choices=[('1', 'Active'), ('0', 'Disabled')], coerce=str)
    submit = SubmitField('Save')

    def validate_username(self, username):
        existing = UserM.check_username(username.data, exclude_id=self.id.data)
        if existing:
            raise ValidationError('Username already taken.')


class SendForm(FlaskForm):
    to = StringField('To', [InputRequired(message='A phone number is required.'), Length(max=32)])
    message = TextAreaField('Message', [
        InputRequired(message='A message is required.'),
        Length(max=640, message='Message is longer than 640 characters.'),
    ])
    submit = SubmitField('Send SMS')
