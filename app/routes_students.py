from app import app, db, models
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request


def unauthorized_entry():
    flash(
        'You were not authorized to enter that website'
    )
    return redirect(url_for('index'))


def get_data():
    try:
        values = request.args.get('values')
        values = eval(values)
    except:
        return None
    if not current_user.is_authenticated \
            or not models.Parameters.query.filter_by(id=values['session_code']).first():
        return None
    return values


@app.route('/students', methods=['GET'])
@login_required
def game_initiate():
    values = get_data()
    if not values:
        return unauthorized_entry()
    values['current'] = 1
    print(values)
    if values['is_pace']:
        values['start_time'] = models.Parameters.query.filter_by(id=values['session_code'])
        return redirect(url_for('game_paced',
                                values=values,
                                current_user=current_user))
    else:
        return redirect(url_for('game_normal',
                                values=values,
                                current_user=current_user))


@app.route('/students/game_normal/<values>', methods=['GET'])
@login_required
def game_normal(values):
    values = eval(values)
    if not values or \
            not current_user.is_authenticated or \
            not models.Parameters.query.filter_by(id=values['session_code']).first():
        return unauthorized_entry()
    current = values['current']
    rounds = values['rounds']
    if current <= rounds:
        demand = values['demand']
        values['current'] += 1
        distribution = list(values['parameters'][current-1].keys())[0]
        if demand[current - 1] == 0:
            sample = values['parameters'][current - 1]['Pool']['sample']
            show = values['parameters'][current - 1]['Pool']['show']
            to_show = []
            for i in range(current - 1 + show, current):
                to_show.append(sample[i])
            demand = sample[show + current - 1]
            return render_template(
                'game/game_normal.html', current_user=current_user,
                values=values, current=current,
                demand=demand, sample=True, distribution=distribution,
                to_show=to_show
            )
        past_demand = demand[0:current-2]
        return render_template(
            'game/game_normal.html', current_user=current_user,
            values=values, past_demand=past_demand,
            rounds=rounds, current=current,
            sample=False, distribution=distribution,
            demand=demand[current - 1]
        )


@app.route('/students/game_normal/<values>', methods=['POST'])
@login_required
def process_game_start(values):
    values = eval(values)


@app.route('/students/game_paced/<values>', methods=['GET'])
@login_required
def game_paced():
    values = get_data()
    if not values or \
            not current_user.is_authenticated or \
            not models.Parameters.query.filter_by(id=values['session_code']).first():
        return unauthorized_entry()
    start_time = values['start_time']
    rounds = values['rounds']
    current = values['current']
    if current <= rounds:
        ws_price = values['wholesale_price']
        r_price = values['retail_price']
        demand = values['demand']
        values['current'] += 1
        return render_template('game/game_paced.html',
                               rounds=rounds, current=current,
                               ws_price=ws_price, r_price=r_price,
                               demand=demand[current - 1],
                               start_time=start_time)
    else:
        return redirect(url_for('game_end', values=values))


@app.route('/student/game_paced', methods=['POST'])
@login_required
def process_paced_action():
    return None


@app.route('/student/game_end', methods=['GET'])
@login_required
def game_end():
    return None
