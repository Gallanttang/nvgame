from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from app import models
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

    def validate_username(self, student_number, session):
        temp_session_code = session.split('_')
        if temp_session_code[0] == 'harishk':
            hashed = int(str(student_number) + '1' + temp_session_code[1])
        elif temp_session_code[0] == 'timh':
            hashed = int(str(student_number) + '2' + temp_session_code[1])
        elif temp_session_code[0] == 'jakez':
            hashed = int(str(student_number) + '3' + temp_session_code[1])
        else:
            raise Exception('Invalid session code')
        user = models.Users.query.filter_by(id=hashed).first()
        print(user)
        if user is None:
            return True
        return False


class InsSignInForm(FlaskForm):
    instructor_id = IntegerField('Instructor ID', validators=[validators.DataRequired()])
    session = StringField('Session Code', validators=[validators.DataRequired()])
    submit = SubmitField('Sign In')


class InputForm(FlaskForm):
    input = IntegerField('Input', validators=[validators.DataRequired()])
    submit = SubmitField('Enter Value')
