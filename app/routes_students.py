from app import app, db, models, routes_all
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request


def unauthorized_entry():
    flash(
        'You were not authorized to enter that website'
    )
    return redirect(url_for('index'))


@app.route('/students', methods=['GET'])
@login_required
def game_start():
    try:
        is_pace = request.args.get('is_pace')
        values = request.args.getlist('values')
        session_code = request.args.get('session_code')
    except:
        return unauthorized_entry()
    if not current_user.is_authenticated or not models.Parameters.query.filter_by(id=session_code).first():
        return unauthorized_entry()
    if is_pace:
        return redirect(url_for('game_paced', values=values, session_code=session_code))
    else:
        return redirect(url_for('game', values=values, session_code=session_code))


@app.route('/students/game_paced', methods=['GET'])
@login_required
def game_paced():
    values = request.args.getlist('values')
    session_code = request.args.get('session_code')
    if not current_user.is_authenticated or not models.Parameters.query.filter_by(id=session_code).first():
        return unauthorized_entry()
    rounds = len(values)

