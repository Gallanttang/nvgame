from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, BooleanField, FloatField
import wtforms.validators as validators


class SignInForm(FlaskForm):
    student_number = IntegerField('Student Number',
                                  validators=[validators.DataRequired(),
                                              validators.number_range(10000000, 99999999)])
    session = StringField('Session Code', validators=[validators.DataRequired()])
    submit = SubmitField('Sign In')


class SignUpForm(FlaskForm):
    student_number = IntegerField('Student Number',
                                  validators=[validators.DataRequired(),
                                              validators.number_range(10000000, 99999999)])
    name = StringField('Preferred name', validators=[validators.DataRequired()])
    session = StringField('Session Code', validators=[validators.DataRequired()])
    submit = SubmitField('Sign In')


class AdminSignInForm(FlaskForm):
    id = StringField('Admin ID', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    submit = SubmitField('Sign In')


class AddAdmin(FlaskForm):
    username = StringField('New Username', validators=[validators.DataRequired()])
    password = StringField('New Password', validators=[validators.DataRequired()])
    name = StringField('Name of Admin', validators=[validators.DataRequired()])
    submit = SubmitField('Create Admin')


class InputForm(FlaskForm):
    input = IntegerField('How many orders?', validators=[validators.DataRequired()])
    submit = SubmitField('Send Order!')
