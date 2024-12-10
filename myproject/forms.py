from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange


class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Please enter your username.'),
            Length(max=50)
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Please enter your password.')]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Please choose a username.'),
            Length(max=50)
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Please create a password.'),
            Length(min=6, message='Password must be at least 6 characters long.')
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.')
        ]
    )
    submit = SubmitField('Register')

class LocationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    activities = StringField('Activities', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ReportForm(FlaskForm):
    activity = SelectField('Select Activity', validators=[DataRequired()])
    submit = SubmitField('Generate Report')
