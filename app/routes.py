from app import app, game
from app import db
from app import admin
from app import models
import app.forms as forms
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required

from app.models import DistributionType


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
        user = models.Users.query.filter_by(sid=unique_key).first()
        if user is None:
            flash('Wrong student number or session code', 'error')
            return redirect(url_for('signIn'))
        login_user(user, remember=True)
        return redirect(url_for('game_start'))
    return render_template('signin.html', title='Sign In', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.SignUpForm()
    if form.validate_on_submit():
        if form.validate_username(form.student_number.data, form.session.data):
            print("invalid details")
            flash('Invalid student number or session code')
            return redirect(url_for('signUp'))
        user = models.Users(id=special_id(form.student_number.data, form.session.data),
                            student_number=form.student_number.data,
                            session_code=form.session.data,
                            pref_name=form.name.data)
        if models.Users.query.filter_by(id=user.id).first() is not None:
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


@app.route('/instructor', methods=['GET', 'POST'])
def instructor_page():
    login = forms.InsSignInForm()
    if current_user.is_authenticated:
        print(current_user.id)
        if current_user.id in admin.adminIDs:
            return redirect('/admin')
    if login.validate_on_submit():
        instructor_id = login.instructor_id.data
        session = login.session.data
        ins_id = special_id(instructor_id, session)
        user = models.Users.query.filter_by(id=ins_id).first()
        if not user or user.id not in admin.adminIDs:
            flash('User not recognized or not found.')
            return redirect(url_for('instructor_page'))
        print(user + 'data received, about to log in')
        login_user(user)
        return redirect('/admin')
    return render_template('/inssignin.html', form=login)


@app.route('/start')
@login_required
def game_start():
    day_index = game.get_day_index(current_user, models.Game)
    current_par = game.get_current_parameters(current_user, models.Parameter)
    current_demand = game.get_current_demand(current_user, models.Demand)
    # redirect consistent pace users
    if current_par.consistent_pace:
        return redirect('/paceloading')
    # protect from finished user coming back and make new orders
    if day_index > current_par.nrounds:
        return redirect(url_for('game_end'))
    history = ''
    previous = ''
    demand_range = ''
    demand_mean = ''
    demand_std_dev = ''
    demand_peak = ''
    if current_par.demand_pattern != DistributionType.SAMPLE_POOL:
        history = current_demand.demand_past
        for x in current_demand.demand_new.split(',')[:day_index - 1]:
            previous = previous + str(x)
        demand_range = str(current_par.distribution_all_lower_bound) \
                       + ' to ' + str(current_par.distribution_all_upper_bound)
    if current_par.demand_pattern == DistributionType.NORMAL:
        demand_mean = current_par.distribution_normal_mean
        demand_std_dev = current_par.distribution_normal_std
    if current_par.demand_pattern == DistributionType.TRIANGULAR:
        demand_peak = current_par.distribution_triangular_peak

    return render_template('game.html',
                           day_index=day_index, current_par=current_par, current_demand=current_demand,
                           history=history, demand_range=demand_range, demand_mean=demand_mean,
                           demand_std_dev=demand_std_dev, demand_peak=demand_peak)


@app.route('/started')
@login_required
def gaming():
    return None


def special_id(ubc_id, session):
    temp_session_code = session.split('_')
    if temp_session_code[0] == 'harishk':
        rv = int(str(ubc_id) + '1' + temp_session_code[1])
    elif temp_session_code[0] == 'timh':
        rv = str(ubc_id) + '2' + temp_session_code[1]
    elif temp_session_code[0] == 'jakez':
        rv = int(str(ubc_id) + '3' + temp_session_code[1])
    else:
        raise Exception('Invalid session code')
    return rv
