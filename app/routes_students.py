from sqlalchemy import and_
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
    if not models.Results.query.filter(and_(models.Results.parameter_id == values['session_code'],
                                            models.Results.user_id == current_user.id,
                                            models.Results.round == values['current']-1)).first():
        result = models.Results(
            parameter_id=values['session_code'],
            user_id=current_user.id, round=values['current']-1,
            distribution=distribution, demanded=demanded,
            time_start=datetime.utcnow(),
            ordered=None, time_answered=None)
        db.session.add(result)
        db.session.commit()


# update the record on the player's order decision
def record_result(values, ordered):
    round_no = values['current'] - 1
    current_time = datetime.utcnow()
    record_to = models.Results.query.filter(
        models.Results.parameter_id == values['session_code'],
        models.Results.user_id == current_user.id,
        models.Results.round == round_no).first()
    if record_to is None:
        print(round_no)
        print(values['session_code'])
        print(current_user.id)
    else:
        record_to.time_answered = current_time
        record_to.ordered = ordered
        db.session.commit()


# This page helps to set up the game depending on the user
# It will find records, if any, on a user and whether they have played the game
# The game will adjust itself based on the results
@app.route('/students', methods=['GET'])
@login_required
def game_initiate():
    values = get_data()
    if not values:
        return unauthorized_entry()
    results = models.Results.query.filter(
        models.Results.user_id == current_user.id,
        models.Results.parameter_id == values['session_code']
    ).all()
    values['current'] = 1
    values['total_profit'] = 0
    if 0 < len(results) < values['rounds']:
        values['current'] = len(results) + 1
        for i, result in enumerate(results):
            if result.ordered is None or not isinstance(result.ordered, int):
                values['current'] = int(result.round)
                break
            ordered = int(result.ordered)
            sold = min(int(result.demanded), int(result.ordered))
            profit = (sold * values['retail_price']) - (ordered * values['wholesale_price'])
            values['total_profit'] += profit
    elif len(results) >= values['rounds']:
        flash('you have already completed this game')
        return redirect(url_for('game_end'))
    session['values'] = values
    if values['is_pace']:
        values['start_time'] = models.Parameters.query.filter_by(id=values['session_code']).first().start_time
        return redirect(url_for('game_paced',
                                current_user=current_user))
    else:
        return redirect(url_for('game_normal',
                                current_user=current_user))


# This function handles the information to display in the game
def game(sec):
    values = get_data()
    if not values or \
            not current_user.is_authenticated or \
            not models.Parameters.query.filter(models.Parameters.id == values['session_code'],
                                               models.Parameters.ongoing == True).first():
        return unauthorized_entry()
    # Moves to helper function for when the session is using treatments 3/4
    if values['treatment'] < 3:
        return game_t12(sec)
    else:
        # Pulls data from the client's session data (it is on their browser)
        current = values['current']
        values['current'] += 1
        rounds = values['rounds']
        treatment = values['treatment']
        demand = values['demand']
        past_demand = demand[0:current - 2]
        if current <= rounds:
            distribution = list(values['parameters'][current - 1].keys())[0]
            if demand[current - 1] == "S":
                sample = values['parameters'][current - 1]['Pool']['sample']
                show = values['parameters'][current - 1]['Pool']['show']
                if show >= len(sample):
                    show = len(sample) - 1
                values['parameters'][current - 1]['Pool']['show'] += 1
                to_show = sample[0:show]
                record_start(values, distribution, sample[show])
                session['values'] = values
                return render_template(
                    'game/game_normal.html', current_user=current_user,
                    values=values, current=current, treatment=treatment,
                    distribution=distribution, is_paced=values['is_pace'], order=True,
                    to_show=to_show, par_no=current-1, sec=sec
                )
            record_start(values, distribution, demand[current - 1])
            session['values'] = values
            distribution = list(values['parameters'][current - 1].keys())[0]
            return render_template(
                'game/game_normal.html', current_user=current_user,
                treatment=treatment, values=values, past_demand=past_demand,
                rounds=rounds, current=current, distribution=distribution,
                sec=sec, par_no=current-1, is_paced=values['is_pace'], order=True
            )
        else:
            return redirect(url_for('game_end'))


# Game mode for treatments 1 and 2
def game_t12(sec):
    values = get_data()
    if not values or \
            not current_user.is_authenticated or \
            not models.Parameters.query.filter(models.Parameters.id == values['session_code'],
                                               models.Parameters.ongoing == True).first():
        return unauthorized_entry()
    current = values['current']
    values['current'] = 1 + current
    rounds = values['rounds']
    treatment = values['treatment']
    demand = values['demand']
    if current <= rounds:
        distribution = list(values['parameters'][0].keys())[0]
        if distribution == "Sample":
            sample = values['parameters'][0]['Pool']['sample']
            show = values['parameters'][0]['Pool']['show']
            to_show = sample[0:show + current]
            record_start(values, distribution, sample[show + current])
            session['values'] = values
            return render_template(
                'game/game_normal.html', current_user=current_user,
                values=values, current=current,
                treatment=treatment,
                distribution=distribution,
                to_show=to_show, par_no=0, is_paced=values['is_pace'],
                sec=sec, order=True
            )
        else:
            record_start(values, distribution, demand[current - 1])
            session['values'] = values
            return render_template(
                'game/game_normal.html', current_user=current_user,
                treatment=treatment, values=values,
                rounds=rounds, current=current, distribution=distribution,
                sec=sec, par_no=0, is_paced=values['is_pace'], order=True
            )
    else:
        return redirect(url_for('game_end'))


# Processes the user input and records their result
def process_game(sec):
    values = get_data()
    if not values or \
            not current_user.is_authenticated or \
            not models.Parameters.query.filter_by(id=values['session_code']).first():
        return unauthorized_entry()
    try:
        ordered = int(request.form['ordered'])
    except:
        ordered = 0
    record_result(values, ordered)
    day = values['current'] - 1
    if values['treatment'] < 3:
        distribution = list(values['parameters'][0].keys())[0]
    else:
        distribution = list(values['parameters'][day-1].keys())[0]
    if distribution == "Pool":
        show = values['parameters'][day-1]['Pool']['show']
        demand = values['parameters'][day-1]['Pool']['sample'][show + 1]
    else:
        demand = values['demand'][day-1]
    sold = int(ordered)
    if int(demand) < int(ordered):
        sold = demand # choose the smaller of the two
    lost = demand - int(ordered) if demand > int(ordered) else 0
    cost = int(ordered) * values['wholesale_price']
    revenue = sold * values['retail_price']
    profit = revenue - cost
    values['total_profit'] += profit
    session['values'] = values
    treatment = values['treatment']
    return render_template('game/game_normal_end.html', values=values,
                           treatment=treatment, sold=sold,
                           ordered=ordered, day=day, lost=lost,
                           cost=cost, revenue=revenue,
                           demand=demand, profit=profit,
                           total_profit=values['total_profit'], sec=sec)


@app.route('/students/game_normal', methods=['GET'])
@login_required
def game_normal():
    return game(0)


@app.route('/students/game_normal', methods=['POST'])
@login_required
def process_game_normal():
    return process_game(0)


@app.route('/students/game_normal_show', methods=['GET'])
def show_results_normal():
    values = get_data()
    ordered = request.form.get('ordered')
    return render_template('game/game_show.html', values=values, ordered=ordered)


@app.route('/students/game_paced', methods=['GET'])
@login_required
def game_paced():
    return game(30000)


@app.route('/students/game_paced', methods=['POST'])
@login_required
def process_game_paced():
    return process_game(30000)


@app.route('/student/game_end', methods=['GET'])
@login_required
def game_end():
    values = get_data()
    return render_template("game/game_normal_complete.html", current_user=current_user,
                           total_profit=values['total_profit'], sec=0,
                           treatment=values['treatment'], is_paced=False)
