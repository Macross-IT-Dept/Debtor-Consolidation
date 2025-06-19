from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import EqualTo, DataRequired, ValidationError
from .models import User
        
class CreateUserForm(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[EqualTo('password', message='Passwords must match'), DataRequired()])
    role = SelectField(label='Role', choices=[('', '-- Select Role --'), ('admin', 'admin'), ('normal', 'normal')], default ='', validators=[DataRequired()])
    submit = SubmitField(label='Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists')        
        
class LoginForm(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Login')

