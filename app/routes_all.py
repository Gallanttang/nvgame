from app import app, db, models
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required


def check_is_admin(user):
    return models.Admins.query.filter_by(id=user.id).first()


def check_user():
    if current_user.is_authenticated:
        if check_is_admin(current_user):
            return redirect(url_for('admin_home'))
        else:
            return redirect(url_for('game_start'))


@app.route('/', methods=['GET', 'POST'])
def index():
    check_user()
    ongoing_sessions = models.Parameters.query.filter_by(ongoing=True).all()
    if ongoing_sessions:
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
    uid = request.form['uid']
    special_id = uid + session_code
    user = models.Users.query.filter_by(id=special_id).first()
    if user:
        login_user(user)
        return redirect(url_for('game_start'))
    else:
        flash('You have the wrong login details!')
        return redirect(url_for('login'))


@app.route('/signup', methods=['GET'])
def signup():
    check_user()
    options = []
    ongoing_sessions = models.Parameters.query.filter_by(ongoing=True).all()
    if ongoing_sessions:
        for session in ongoing_sessions:
            options.append(session.id)
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
        return redirect(url_for('game_start'))


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been successfully logged out!')
    return redirect(url_for('index'))
