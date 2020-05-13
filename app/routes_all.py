import json
import numpy as np
from app import app, db, models
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user


def check_is_admin(user):
    return models.Admins.query.filter_by(id=user.id).first()


def check_user():
    if current_user.is_authenticated:
        if check_is_admin(current_user):
            return redirect(url_for('admin_home'))
        else:
            return redirect(url_for('game_start'))


def generate_demand_same_distribution(distribution_type, distribution, rounds):
    if distribution_type == 'Normal':
        return np.random.normal(distribution['mean'], distribution['standard_deviation'], rounds)
    if distribution_type == 'Triangular':
        return np.random.triangular(distribution['lower_bound'],
                                    distribution['peak'],
                                    distribution['upper_bound'], 0)
    if distribution_type == 'Uniform':
        return np.random.uniform(distribution['lower_bound'], distribution['upper_bound'], 0)
    if distribution_type == 'Pool':
        return distribution['sample']


def generate_demand(session):
    session = models.Parameters.query.filter_by(id=session).first()
    did = session.detail_id
    detail = models.Details.query.filter_by(id=did).first()
    with open('/app/distributions/'+detail.distribution_file) as json_file:
        data = json.load(json_file)
        rounds = data['rounds']
        if data['treatment'] < 3:
            # will use one type of distribution to create demand for all rounds
            distribution = data['parameters'][0].keys()[0]
            par = data['parameters'][0][distribution]
            return generate_demand_same_distribution(distribution, par, rounds)
        else:
            # each round has a different type of demand distribution
            parameters = data['parameters']
            demand = []
            for parameter in parameters:
                key = parameter.keys()[0]
                demand.append(generate_demand_same_distribution(key, parameter, 1)[0])
            return demand


def has_ongoing_session():
    return models.Parameters.query.filter_by(ongoing=True).all()


@app.route('/', methods=['GET', 'POST'])
def index():
    check_user()
    if has_ongoing_session():
        return render_template('welcome.html', qualified=True, current_user=current_user)
    else:
        return render_template('welcome.html', qualified=False, current_user=current_user)


@app.route('/login', methods=['GET'])
def login():
    sessions = models.Parameters.query.filter_by(ongoing=True).all()
    if sessions:
        options = []
        for option in sessions:
            options.append(option.id)
        length = len(options)
        return render_template('login.html', options=options, length=length, current_user=current_user)
    else:
        flash('There are no ongoing sessions at the moment!')
        return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def process_login():
    session_code = request.form['session_code']
    is_pace = models.Parameters.query.filter_by(id=session_code).first().is_pace
    uid = request.form['uid']
    special_id = uid + session_code
    user = models.Users.query.filter_by(id=special_id).first()
    if user:
        login_user(user)
        values = generate_demand(session_code)
        return redirect(url_for('game_start', value=values,
                                is_pace=is_pace, session_code=session_code))
    else:
        flash('You have the wrong login details!')
        return redirect(url_for('login'))


@app.route('/signup', methods=['GET'])
def signup():
    check_user()
    options = []
    ongoing_sessions = has_ongoing_session()
    if ongoing_sessions:
        for session in ongoing_sessions:
            options.append(session.id)
    else:
        return redirect(url_for('index'))
    return render_template('signup.html', options=options, current_user=current_user)


@app.route('/signup', methods=['POST'])
def process_signup():
    session_code = request.form['session_code']
    uid = str(request.form['uid'])
    name = request.form['name']
    if len(uid) != 8:
        flash('Incorrect student number!')
        return redirect(url_for('signup'))
    special_id = uid + session_code
    if len(special_id) <= 14:
        check = models.Users.query.filter_by(id=special_id).first()
        if check:
            login_user(check)
            redirect(url_for('game_start'))
        new_user = models.Users(id=special_id, admin=False, name=name)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        is_pace = models.Parameters.query.filter_by(id=session_code).first().is_pace
        values = generate_demand(session_code)
        return redirect(url_for('game_start', value=values,
                                is_pace=is_pace, session_code=session_code))


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been successfully logged out!')
    return redirect(url_for('index'))
