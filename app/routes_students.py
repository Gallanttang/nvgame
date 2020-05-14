from app import app, db, models
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
        values = request.args.get('value')
        values = eval(values)
    except:
        return unauthorized_entry()
    if not current_user.is_authenticated \
            or not models.Parameters.query.filter_by(id=values['session_code']).first():
        return unauthorized_entry()
    return values
    # if is_pace:
    #   return redirect(url_for('game_paced', values=values))
    # else:
    #   return redirect(url_for('game', values=values))


@app.route('/students/game_paced', methods=['GET'])
@login_required
def game_paced():
    values = request.args.getlist('values')
    session_code = request.args.get('session_code', None)
    rounds = len(values)
    if not current_user.is_authenticated or not models.Parameters.query.filter_by(id=session_code).first():
        return unauthorized_entry()
