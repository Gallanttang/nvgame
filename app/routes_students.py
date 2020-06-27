from app import app, db, models
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request, session
from datetime import datetime


def unauthorized_entry():
    flash(
        'You were not authorized to enter that website'
    )
    return redirect(url_for('index'))


def get_data():
    if 'values' in session:
        values = session['values']
    else:
        return None
    if not current_user.is_authenticated \
            or not models.Parameters.query.filter(models.Parameters.id == values['session_code'],
                                                  models.Parameters.ongoing == True).first():
        return None
    return values


# record the player's condition at the start of the round
def record_start(values, distribution, demanded):
    # unique_id = current_user.id + str(values['current'])
    result = models.Results(
        parameter_id=values['session_code'],
        user_id=current_user.id, round=values['current'],
        distribution=distribution, demanded=demanded,
        time_start=datetime.utcnow(),
        ordered=None, time_answered=None)
    db.session.add(result)
    db.session.commit()


# update the record on the player's order decision
def record_result(values, ordered):
    unique_id = current_user.id + str(values['current'])
    current_time = datetime.utcnow()
    record_to = models.Results.query.filter_by(id=unique_id).first()
    record_to.time_answered = current_time
    record_to.ordered = ordered
    db.session.commit()


@app.route('/students', methods=['GET'])
@login_required
def game_initiate():
    values = get_data()
    print(values)
    if not values:
        return unauthorized_entry()
    values['current'] = 1
    values['total_profit'] = 0
    session['values'] = values
    if values['is_pace']:
        values['start_time'] = models.Parameters.query.filter_by(id=values['session_code']).first().start_time
        return redirect(url_for('game_paced',
                                current_user=current_user))
    else:
        return redirect(url_for('game_normal',
                                current_user=current_user))


@app.route('/students/game_normal', methods=['GET'])
@login_required
def game_normal():
    values = get_data()
    if not values or \
            not current_user.is_authenticated or \
            not models.Parameters.query.filter(models.Parameters.id == values['session_code'],
                                               models.Parameters.ongoing == True).first():
        return unauthorized_entry()
    current = values['current']
    rounds = values['rounds']
    if current <= rounds:
        demand = values['demand']
        values['current'] += 1
        distribution = list(values['parameters'][current - 1].keys())[0]
        past_demand = demand[0:current - 2]
        record_start(values, distribution, demand)
        if demand[current - 1] == 0:
            sample = values['parameters'][current - 1]['Pool']['sample']
            show = values['parameters'][current - 1]['Pool']['show']
            to_show = []
            for i in range(current - 1 + show, current):
                to_show.append(sample[i])
            session['values'] = values
            return render_template(
                'game/game_normal.html', current_user=current_user,
                values=values, current=current,
                distribution=distribution,
                to_show=to_show
            )
        session['values'] = values
        return render_template(
            'game/game_normal.html', current_user=current_user,
            values=values, past_demand=past_demand,
            rounds=rounds, current=current, distribution=distribution
        )
    else:
        return redirect(url_for('game_end'))


@app.route('/students/game_normal', methods=['POST'])
@login_required
def process_game_normal():
    values = get_data()
    if not values or \
            not current_user.is_authenticated or \
            not models.Parameters.query.filter_by(id=values['session_code']).first():
        return unauthorized_entry()
    ordered = request.form['ordered']
    record_result(values, ordered)
    day = values['current']
    demand = values['demand'][day - 1]
    sold = demand if demand < ordered else ordered  # choose the smaller of the two
    lost = demand - ordered if demand > ordered else 0
    cost = ordered * values['wholesale_price']
    revenue = sold * values['retail_price']
    profit = revenue - cost
    values['total_profit'] += profit
    session['values'] = values
    return render_template('game/game_normal_end.html',
                           ordered=ordered, day=day, lost=lost,
                           cost=cost, revenue=revenue,
                           demand=demand, profit=profit,
                           total_profit=values['total_profit'])


@app.route('/students/game_normal_show', methods=['GET'])
def show_results_normal():
    values = get_data()
    ordered = request.form.get('ordered')
    return render_template('game/game_show.html', values=values, ordered=ordered)


@app.route('/students/game_paced', methods=['GET'])
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
def process_game_paced():
    return None


@app.route('/student/game_end', methods=['GET'])
@login_required
def game_end():
    values = get_data()
    return render_template("game/game_normal_end.html", current_user=current_user,
                           total_profit=values['total_profit'])
