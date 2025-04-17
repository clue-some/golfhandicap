from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError
from handicap.models import User

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[Optional(), Length(min=0, max=50)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(check_deliverability=True)])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=40)])
    password_repeat = PasswordField('Repeat Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    handicap_index = FloatField('Handicap Index (if known, otherwise leave blank.)', validators=[Optional(), NumberRange(max=54.0)])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('This email address is already being used.')
        
class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                              validators=[DataRequired()])
    remember = BooleanField('Stay Logged In') # Use secure cookie
    submit = SubmitField('Login')

class AccountForm(FlaskForm):
    name = StringField('Name', validators=[Optional(), Length(min=0, max=50)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(check_deliverability=True)])
    picture = FileField('Change Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('This email address is already being used.')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is None:
            raise ValidationError('The email address is not registered on this site.')
        
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=6, max=40)])
    password_repeat = PasswordField('Repeat Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')