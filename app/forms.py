from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, HiddenField
from wtforms.validators import EqualTo, DataRequired, ValidationError, Optional
from .models import User

class UniqueForEdit:

    def __init__(self, model, field, message="This value is already in use."):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field_to_validate):

        user_id = form.user_id.data

        existing_record = self.model.query.filter(
            self.field == field_to_validate.data,
            self.model.id != user_id # Exclude the current user's ID
        ).first()

        if existing_record:
            raise ValidationError(self.message)
        
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

class EditUserForm(FlaskForm):
    user_id = HiddenField()
    username = StringField(label='Username', validators=[Optional(), UniqueForEdit(User, User.username, message='Username already exists')])
    password = PasswordField(label='Password', validators=[Optional()])
    confirm_password = PasswordField(label='Confirm Password', validators=[EqualTo('password', message='Passwords must match')])
    role = SelectField(label='Role', choices=[('', '-- Select Role --'), ('admin', 'admin'), ('normal', 'normal')], validators=[Optional()], default ='')
    submit = SubmitField(label='Edit')    
        
class LoginForm(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Login')

