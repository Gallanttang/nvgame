from app import app, game
from app import db
from app import admin
from app import models
import app.forms as forms
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
import pandas as pd


def special_id(ubc_id, session):
    temp_session_code = session.split('_')
    if temp_session_code[0] == 'harishk':
        rv = int(str(ubc_id) + '1' + temp_session_code[1])
    elif temp_session_code[0] == 'timh':
        rv = str(ubc_id) + '2' + temp_session_code[1]
    elif temp_session_code[0] == 'test':
        rv = int(str(ubc_id) + '3' + temp_session_code[1])
    else:
        raise Exception('Invalid session code')
    return rv


@app.route('/')
def index():
    return render_template('welcome.html', current_user=current_user, game=url_for('game_start'))


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
    return render_template('login.html', title='Sign In', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.SignUpForm()
    if form.validate_on_submit():
        sid = ''
        try:
            sid = special_id(form.student_number.data, form.session.data)
        except:
            flash('Invalid student number or session code.')
            redirect(url_for('signUp'))
        user = models.Users(id=sid,
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
    return render_template('/admin_login.html', form=login)


def start_round(form, dest):
    day_index = game.get_day_index(current_user, models.Game)
    current_par = game.get_current_parameters(current_user, models.Parameter)
    current_demand = game.get_current_demand(current_user, models.Demand)
    # redirect consistent pace users
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
    return render_template(dest, form=form,
                           day_index=day_index, current_par=current_par, current_demand=current_demand,
                           history=history, demand_range=demand_range, demand_mean=demand_mean,
                           demand_std_dev=demand_std_dev, demand_peak=demand_peak)


def end_round(form, dest):
    day_index = game.get_day_index(current_user, models.Game)
    current_par = game.get_current_parameters(current_user, models.Parameter)
    current_demand = game.get_current_demand(current_user, models.Demand)
    norder = int(form.input.data)
    ndemand = int(current_demand.demand_new.split(',')[day_index - 1])
    nsold = min(norder, ndemand)
    nlost = max(0, ndemand - norder)
    rev = round(nsold * round(float(current_par.retail_price), 2), 2)
    cost = round(norder * round(float(current_par.wholesale_price), 2), 2)
    profit = round(rev - cost, 2)
    if day_index == 1:
        total_profit = round(profit, 2)
    else:
        total_profit = round(profit
                             + models.Game.query.filter_by(id=current_user.id,
                                                               day_index=day_index - 1).first().total_profit, 2)
    # insert into db
    current_game_rec = models.Game(session_code=current_user.session_code,
                                       id=current_user.id,
                                       pname=current_user.pname,
                                       day_index=day_index,
                                       norder=norder,
                                       ndemand=ndemand,
                                       nsold=nsold,
                                       nlost=nlost,
                                       rev=rev,
                                       cost=cost,
                                       profit=profit,
                                       total_profit=total_profit)
    db.session.add(current_game_rec)
    db.session.commit()
    return render_template(dest, norder=norder, ndemand=ndemand,
                           nsold=nsold, nlost=nlost, rev=rev, cost=cost,
                           current_par=current_par, profit=profit,
                           tot_profit=total_profit)


@app.route('/game', methods=['GET', 'POST'])
@login_required
def game_start():
    form = forms.InputForm()
    day_index = game.get_day_index(current_user, models.Game)
    current_par = game.get_current_parameters(current_user, models.Parameter)
    if current_par.consistent_pace:
        return redirect('/paceloading')
    # protect from finished user coming back and make new orders
    if day_index > current_par.nrounds:
        return redirect(url_for('game_end'))
    if form.validate_on_submit():
        return end_round(form, 'roundend.html')
    else:
        return start_round(form, 'game.html')


import matplotlib.pyplot as plt
import numpy as np
from base64 import b64encode
import io


# show accumulated game stats in plot at the end of each day
def show_plot_stats_html(resdf, day_index):
    # get data from df
    day_data = list(resdf['Day #'])
    order_data = list(resdf['Order Placed'])
    demand_data = list(resdf['Customer Demand'])
    profit_data = list(resdf['Profit'])
    # start of plot
    # left ax
    sauder_green = (120 / 255, 190 / 255, 32 / 255)
    fig, ax1 = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(sauder_green)
    ax1.set_facecolor(sauder_green)
    ax1.set_xlabel('Days')
    ax1.set_ylabel('Qty', color='black')
    l1, = ax1.plot(day_data, order_data, marker='o', color='purple', linewidth=1, label='Order Qty')
    l2, = ax1.plot(day_data, demand_data, marker='o', color='red', linewidth=1, label='Demand Qty')
    ax1.tick_params(axis='y', labelcolor='black')
    # right ax
    ax2 = ax1.twinx()
    ax2.set_ylabel('Profit', color='blue')
    l3, = ax2.plot(day_data, profit_data, marker='o', color='blue', linewidth=1, label='Profit')
    ax2.tick_params(axis='y', labelcolor='blue')
    plt.xticks(np.arange(1, day_index + 1, 1))
    plt.legend([l1, l2, l3], ['Order Qty', 'Demand Qty', 'Profit'], bbox_to_anchor=(1.15, 1), loc=2, frameon=False,
               facecolor=sauder_green)
    fig.tight_layout()
    # figure to html
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    img.seek(0)
    encoded = b64encode(img.getvalue())
    fig_html = '<img src="data:image/png;base64, {}">'.format(encoded.decode('utf-8'))
    return fig_html


@app.route('/stats', methods=['GET', 'POST'])
@login_required
def stats():
    # extract info
    day_index = len(models.Game.query.filter_by(id=current_user.id).all())
    current_par = models.Parameter.query.filter_by(session_code=current_user.session_code).all()[-1]
    # redirect consistent pace users
    if current_par.consistent_pace:
        return redirect(url_for('pace_loading'))
    # protect from new user visiting this page before make any decision
    if day_index == 0:
        return redirect(url_for('day_start'))
    # db to df
    db_connect = db.create_engine(app.config['SQLALCHEMY_DATABASE_URI']).connect()
    if current_par.game_type == 2 or current_par.game_type == 4:
        resdf = pd.read_sql_query('''SELECT day_index,norder,ndemand,nsold,nlost
                                     FROM game
                                     WHERE id = {}'''.format(current_user.id), db_connect)
        resdf = resdf.rename(
            columns={'day_index': 'Day #', 'norder': 'Order Placed', 'ndemand': 'Customer Demand', 'nsold': 'Sold',
                     'nlost': 'Lost Sales'})
    else:
        resdf = pd.read_sql_query('''SELECT day_index,norder,ndemand,nsold,nlost,profit,total_profit
                                     FROM game
                                     WHERE id = {}'''.format(current_user.id), db_connect)
        resdf = resdf.rename(
            columns={'day_index': 'Day #', 'norder': 'Order Placed', 'ndemand': 'Customer Demand', 'nsold': 'Sold',
                     'nlost': 'Lost Sales', 'profit': 'Profit', 'total_profit': 'Total Profit'})
    db_connect.close()
    html = resdf.to_html(index=False)
    plot = resdf.show_plot_stats_html(resdf, day_index)
    return render_template('stats.html', html=html, plot=plot, day_index=day_index)


@app.route('/end')
@login_required
def end():
    # extract info
    day_index = len(models.Game.query.filter_by(id=current_user.id).all())
    current_par = models.Parameter.query.filter_by(session_code=current_user.session_code).all()[-1]
    # redirect consistent pace users
    if current_par.consistent_pace:
        return redirect(url_for('pace_loading'))
    # protect from users accessing this page until they are done (day_index = nrounds)
    if day_index < current_par.nrounds:
        return redirect(url_for('show_stats'))


@app.route('/paceloading', methods=['GET', 'POST'])
@login_required
def pace_loading():
    # users for unpaced sessions are not allowed
    current_par = models.Parameter.query.filter_by(session_code=current_user.session_code).all()[-1]
    if not current_par.consistent_pace:
        return redirect(url_for('stats'))
    # users for paced sessions are allowed but returns depend on conditions
    try:
        # instructor not yet opened the paced session if exception raised
        cur_pace = models.Pace.query.filter_by(session_code=current_user.session_code).first()
        participants = cur_pace.session_id_collection.split(',')
        if current_user.id in participants:
            condition = True
        else:
            condition = False
        return render_template('pace_loading.html', condition=condition)
    except:
        return render_template('pace_loading_failed.html')


# paced game run page 1
# ask for order size
@app.route('/pace_run', methods=['GET'])
@login_required
def pace_day_start(form):
    day_index = game.get_day_index(current_user, models.Game)
    current_par = game.get_current_parameters(current_user, models.Parameter)
    current_demand = game.get_current_demand(current_user, models.Demand)
    # users for unpaced sessions are not allowed
    if not current_par.consistent_pace:
        return redirect('/stats')
    # users for paced sessions are allowed but returns depend on conditions
    try:
        # instructor not yet opened the paced session if exception raised
        current_pace = game.get_current_pace(current_user, models.Pace)
        # id in collection
        if current_user.id in [int(x) for x in current_pace.session_id_collection.split(',')]:
            pass
        else:  # id not in collection
            return redirect('/paceloading')
    except:
        return redirect('/paceloading')
    # pace control
    if day_index - 1 != min([len(models.Game.query.filter_by(id=y).all()) for y in
                             [int(x) for x in current_pace.session_id_collection.split(',')]]):
        return redirect('/pacewaiting')
        # protect from finished user coming back and make new orders
    if day_index > current_par.nrounds:
        return redirect(url_for('pace_game_end'))
    nrounds = int(current_par.nrounds)
    wholesale_price = round(float(current_par.wholesale_price), 2)
    retail_sale_price = round(float(current_par.retail_price), 2)
    demand_pattern = 'FROM ' + str(current_par.demand_pattern).split('.')[1].replace('_', ' ')
    distri_null = '' if current_par.demand_pattern == DistributionType.SAMPLE_POOL else 'DISTRIBUTION'
    history = '<p>Historical Demand Samples: {}</p>'.format(
        current_demand.demand_past) if current_par.demand_pattern == DistributionType.SAMPLE_POOL else ''
    previous = '<p>Demands From Previous Rounds: {}</p>'.format(
        str([int(x) for x in current_demand.demand_new.split(',')][:day_index - 1])[1:-1]) \
                   if current_par.demand_pattern == DistributionType.SAMPLE_POOL else '',
    demand_range = '' if current_par.demand_pattern == DistributionType.SAMPLE_POOL \
                       else '<p>Demand Range: {}</p>'.format(
                        str(current_par.distribution_all_lower_bound) +
                        ' to ' + str(current_par.distribution_all_upper_bound)),
    demand_mean = '<p>Demand Mean: {}</p>'.format(
        current_par.distribution_normal_mean) if current_par.demand_pattern == DistributionType.NORMAL else '',
    demand_std = '<p>Demand Standard Deviation: {}</p>'.format(
        current_par.distribution_normal_std) if current_par.demand_pattern == DistributionType.NORMAL else '',
    demand_peak = '<p>Demand Peak: {}</p>'.format(
        current_par.distribution_triangular_peak) if current_par.demand_pattern == DistributionType.TRIANGULAR else '',
    day = day_index
    return render_template('pace_day_start.html', form=form, nrounds=nrounds, wholesale_price=wholesale_price,
                           retail_sale_price=retail_sale_price, demand_pattern=demand_pattern,
                           distri_null=distri_null, history=history, previous=previous,
                           demand_range=demand_range, demand_mean=demand_mean, demand_std=demand_std,
                           demand_peak=demand_peak, day=day)


# paced game run page 2
# show result based on inventory ordered
@app.route('/pacerun', methods=['GET', 'POST'])
@login_required
def pace_day():
    form = forms.InputForm()
    day_index = game.get_day_index(current_user, models.Game)
    current_par = game.get_current_parameters(current_user, models.Parameter)
    # users for unpaced sessions are not allowed
    if not current_par.consistent_pace:
        return redirect('/stats')
    # users for paced sessions are allowed but returns depend on conditions
    try:
        # instructor not yet opened the paced session if exception raised
        current_pace = game.get_current_pace(current_user, models.Pace)
        # id in collection
        if current_user.id in [int(x) for x in current_pace.session_id_collection.split(',')]:
            pass
        else:  # id not in collection
            return redirect(url_for('pace_loading'))
    except:
        return redirect(url_for('pace_loading'))
    # pace control
    if day_index - 1 != min([len(models.Game.query.filter_by(id=y).all()) for y in
                             [int(x) for x in current_pace.session_id_collection.split(',')]]):
        return redirect(url_for('pace_loading'))
    # protect from finished user coming back and make new orders
    if day_index > current_par.nrounds:
        return redirect(url_for('pace_game_end'))

    if form.validate_on_submit():
        return end_round(form, 'pace_day_end.html')
    else:
        return start_round(form, 'pace_day_start.html')


@app.route('/pacewaiting', methods=['GET', 'POST'])
@login_required
def pace_waiting():
    # extract info
    day_index = game.get_day_index(current_user, models.Game)
    current_par = game.get_current_parameters(current_user, models.Parameter)
    # users for unpaced sessions are not allowed
    if not current_par.consistent_pace:
        return redirect('/stats')
    # users for paced sessions are allowed but returns depend on conditions
    try:
        # instructor not yet opened the paced session if exception raised
        current_pace = models.Pace.query.filter_by(session_code=current_user.session_code).all()[-1]
        # id in collection
        if current_user.id in [int(x) for x in current_pace.session_id_collection.split(',')]:
            pass
        else:  # id not in collection
            return redirect(url_for('pace_loading'))
    except:
        return redirect(url_for('pace_loading'))
    # pace control
    condition = day_index - 1 != min([len(models.Game.query.filter_by(id=y).all())
                                      for y in [int(x) for x in current_pace.session_id_collection.split(',')]])
    return render_template('pace_wait.html', condition=condition)
