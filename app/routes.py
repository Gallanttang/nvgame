from werkzeug.urls import url_parse

from app import app
from app import db
from app import admin
from app.models import User
import app.forms as forms
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required


@app.route('/')
def index():
    return render_template('welcome.html', current_user=current_user)


@app.route('/signin', methods=['GET', 'POST'])
def signIn():
    if current_user.is_authenticated:
        return redirect('/game')
    form = forms.SignInForm()
    if form.validate_on_submit():
        flash('Login requested for student {}, session {}'.format(
            form.student_number.data, form.session.data))
        # Used to allow the same student to participate in different sessions
        unique_key = special_id(form.student_number.data, form.session.data)
        user = User.query.filter(User.id == unique_key).first()
        if user is None:
            flash('Wrong student number or session code', 'error')
            return redirect(url_for('signIn'))
        login_user(user, remember=True)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('signin.html', title='Sign In', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.SignUpForm()
    if form.validate_on_submit():
        flash('Creating account for student {}, session {}').format(form.name, form.session)
        if not form.validate_username(form.student_number.data, form.session.data):
            flash('Invalid student id or session code')
            return redirect(url_for('signUp'))
        unique_id = special_id(form.student_number, form.session.data)
        user = User(id=unique_id,
                    student_number=form.student_number.data,
                    session_code=form.session.data,
                    pref_name=form.name.data)
        if User.query.filter_by(User.id == unique_id).first() is not None:
            flash('You have already created an account, logging in now.')
            login_user(user)
            return redirect(url_for('game_start'))
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        login_user(user)
        return redirect(url_for('game_start'))
    return render_template('signup.html', title='Sign Up', form=form)


@app.route('/signout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/instructor')
def instructor_page():
    login = forms.InsSignInForm()
    if current_user.student_number in admin.adminIDs:
        return redirect('/admin')
    if login.validate_on_submit():
        instructor_id = login.instructor_id.data
        session = login.session.data
        ins_id = special_id(instructor_id, session)
        user = User.query.filter_by(id=ins_id).first()
        if not (user and user.id in admin.adminIDs):
            flash('User not recognized or not found.')
            return redirect(url_for('instructor_page'))
        login_user(user)
        return redirect('/admin')
    return render_template('instructor_page', form=login)


@app.route('/start')
@login_required
def game_start():
    return render_template('game.html')


def special_id(ubc_id, session):
    temp_session_code = session.split('_')
    if temp_session_code[0] == 'harishk':
        id = int(str(ubc_id) + '1' + temp_session_code[1])
    elif temp_session_code[0] == 'timh':
        id = int(str(ubc_id) + '2' + temp_session_code[1])
    elif temp_session_code[0] == 'jakez':
        id = int(str(ubc_id) + '3' + temp_session_code[1])
    else:
        raise Exception('Invalid session code')
    return id

