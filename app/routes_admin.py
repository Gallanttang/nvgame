from app import app, models, db, forms, tables
from flask import render_template, flash, redirect, url_for, request
import os
import shutil
import json
from flask_login import current_user, login_user, login_required


def check():
    user = models.Admins.query.filter_by(id=current_user.id).first()
    if not user:
        flash('You are not an admin user, ' +
              'please contact the administrators for more details.')
        return True
    return False


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    login = forms.AdminSignInForm()
    if current_user.is_authenticated:
        user = models.Admins.query.filter_by(id=current_user.id).first()
        if user:
            return redirect(url_for('admin_home'))
        else:
            flash('You are not an instructor!')
            return redirect(url_for('index'))
    if login.validate_on_submit():
        instructor_id = login.id.data
        password = login.password.data
        user = models.Admins.query.filter(models.Admins.id == instructor_id,
                                          models.Admins.password == password,
                                          models.Admins.active == True).first()
        if not user:
            flash('Admin login details not recognized, deactivated, or incorrect.')
            return redirect(url_for('admin_login'))
        user = models.Users.query.filter_by(id=instructor_id).first()
        login_user(user)
        return redirect(url_for('admin_home'))
    return render_template('admin/admin_login.html', form=login, current_user=current_user)


@app.route('/admin/home', methods=['GET', 'POST'])
@login_required
def admin_home():
    if check():
        return redirect(url_for('admin_login'))
    return render_template('admin/admin_home.html', current_user=current_user)


@app.route('/admin/add_admin', methods=['GET', 'POST'])
@login_required
def add_admin():
    if check():
        return redirect(url_for('admin_login'))
    form = forms.AddAdmin()
    if form.validate_on_submit():
        new_id = form.username.data
        password = form.password.data
        name = form.name.data
        user = models.Admins.query.filter_by(id=new_id).first()
        if not user:
            new_user = models.Users(id=new_id, admin=True, name=name)
            new_admin = models.Admins(id=new_id, password=password, active=True)
            db.session.add(new_user)
            db.session.commit()
            db.session.add(new_admin)
            db.session.commit()
            flash(new_id + ' is now an admin')
        else:
            flash('This username has already been taken, try a different one')
            return redirect(url_for('add_admin'))
        return redirect(url_for('admin_home'))
    return render_template('admin/add_admin.html', form=form, current_user=current_user)


@app.route('/admin/deactivate_admin', methods=['GET'])
@login_required
def deactivate_admin():
    if check():
        return redirect(url_for('admin_login'))
    actives = models.Admins.query.filter_by(active=True).all()
    if len(actives) < 1:
        choices = []
        for option in actives:
            choices.append(option.id)
        length = len(choices)
        return render_template('admin/deactivate_admin.html',
                               choices=choices, current_user=current_user,
                               length=length)
    else:
        flash('There are no other active users right now. Hence, you cannot deactivate this user')
        return redirect(url_for('admin_home'))


@app.route('/admin/deactivate_admin', methods=['POST'])
@login_required
def process_deactivate_admin():
    to_deactivate = request.form['choice']
    models.Admins.filter_by(id=to_deactivate).update(dict(active=False))
    db.session.commit()
    flash('The admin user ' + to_deactivate + 'has been deactivated successfully')
    return redirect(url_for('admin_home'))


@app.route('/admin/reactivate_admin', methods=['GET'])
@login_required
def reactivate_admin():
    if check():
        return redirect(url_for('admin_login'))
    options = models.Admins.query.filter_by(active=False).all()
    if not options:
        flash('There are no inactive users right now.')
        return redirect(url_for('admin_home'))
    choices = []
    for option in options:
        choices.append(option)
    length = len(choices)
    return render_template('admin/reactivate_admin.html', qualified=True,
                           choices=choices, current_user=current_user,
                           length=length)


@app.route('/admin/reactivate_admin', methods=['POST'])
@login_required
def process_reactivate_admin():
    to_reactivate = request.form['choice']
    models.Admins.filter_by(id=to_reactivate).update(dict(active=False))
    db.session.commit()
    flash('The admin user ' + to_reactivate + ' has been reactivated successfully')
    return redirect(url_for('admin_home'))


@app.route('/admin/add_session', methods=['GET'])
@login_required
def add_session():
    if check():
        return redirect(url_for('admin_login'))
    choices = []
    details = models.Details.query.all()
    if not details:
        flash('No game templates found, please add one before creating a session')
        return redirect(url_for('admin_home'))
    for did in details:
        choices.append(did.id)

    table = tables.Detail(details)
    table.border = True
    return render_template('admin/add_session.html',
                           current_user=current_user,
                           choices=choices,
                           table=table)


@app.route('/admin/add_session', methods=['POST'])
@login_required
def process_add_session():
    count = len(models.Parameters.query.filter_by(admin=current_user.id).all()) + 1
    pid = current_user.id + str(count)
    detail_id = request.form['choice']
    is_pace = False
    if request.form.get('is_pace') == "1":
        is_pace = True
    print(request.form.get('is_pace'))
    par = models.Parameters(id=pid, admin=current_user.id, is_pace=is_pace,
                            detail_id=detail_id, start_time=None)
    db.session.add(par)
    db.session.commit()
    flash('New session ' +
          pid +
          ' has been created! Please start the session if it is paced.')
    return redirect(url_for('admin_home'))


@app.route('/admin/start_session', methods=['GET'])
@login_required
def start_session():
    if check():
        return redirect(url_for('admin_login'))
    choices = []
    param = models.Parameters.query.filter(models.Parameters.ongoing == True and
                                           models.Parameters.start_time is None).all()
    if not param:
        flash('No active sessions that were not yet started were found.')
        return redirect(url_for('admin_home'))
    for pid in param:
        choices.append(pid.id)
    table = tables.Parameter(param)
    table.border = True
    return render_template('admin/stop_session.html',
                           table=table, current_user=current_user)


@app.route('/admin/stop_session', methods=['POST'])
@login_required
def process_stop_session():
    if check():
        return redirect(url_for('admin_login'))
    choice = request.form['choice']
    stopping = models.Parameters.query.filter_by(id=choice)
    stopping.ongoing = False
    db.session.commit()
    flash('The session ' + choice + ' has been ended')
    return redirect(url_for('admin_home'))


@app.route('/admin/stop_session', methods=['GET'])
@login_required
def stop_session():
    if check():
        return redirect(url_for('admin_login'))
    choices = []
    param = models.Parameters.query.filter_by(ongoing=True).all()
    if not param:
        flash('No active sessions were found.')
        return redirect(url_for('admin_home'))

    for pid in param:
        choices.append(pid.id)
    table = tables.Parameter(param)
    table.border = True
    return render_template('admin/stop_session.html',
                           table=table, current_user=current_user)


@app.route('/admin/stop_session', methods=['POST'])
@login_required
def process_stop_session():
    if check():
        return redirect(url_for('admin_login'))
    choice = request.form['choice']
    stopping = models.Parameters.query.filter_by(id=choice)
    stopping.ongoing = False
    db.session.commit()
    flash('The session ' + choice + ' has been ended')
    return redirect(url_for('admin_home'))


@app.route('/admin/add_detail', methods=['GET'])
@login_required
def add_detail():
    if check():
        return redirect(url_for('admin_login'))
    distribution_path = os.getcwd() + '/app/distributions'
    distributions = []
    for f in os.listdir(distribution_path):
        if os.path.isfile(os.path.join(distribution_path, f)):
            distributions.append(f)
    if len(distributions) < 1:
        flash('Create a distribution file first!')
        return redirect(url_for('admin_home'))
    else:
        return render_template('admin/add_detail.html',
                               current_user=current_user,
                               distributions=distributions)


@app.route('/admin/add_detail', methods=['POST'])
@login_required
def process_add_detail():
    print(request.form)
    did = current_user.id + '_' + str(len(models.Details.query.filter(
        models.Details.id.match(current_user.id + "%")).all()))
    distribution_file = request.form['distribution_file']
    description = request.form['description']
    new_detail = models.Details(id=did,
                                distribution_file=distribution_file,
                                description=description)
    db.session.add(new_detail)
    db.session.commit()
    flash('You have successfully added the new detail ' + did + '!')
    return redirect(url_for('admin_home'))


@app.route('/admin/remove_detail', methods=['GET'])
@login_required
def remove_detail():
    if check():
        return redirect(url_for('admin_login'))
    details = models.Details.query.all()
    if not details:
        flash('You do not have any details to delete!')
        return redirect(url_for('admin_home'))
    table = tables.Detail(details)
    table.border = True
    choices = []
    for did in details.id:
        choices.append(did)
    return render_template('admin/remove_detail.html', table=table,
                           choices=choices, current_user=current_user)


@app.route('/admin/add_distribution', methods=['GET'])
@login_required
def add_distribution():
    if check():
        return redirect(url_for('admin_login'))
    return render_template('admin/add_distribution.html', current_user=current_user)


@app.route('/admin/add_distribution', methods=['POST'])
@login_required
def process_add_distribution():
    if check():
        return redirect(url_for('admin_login'))
    treatment = int(request.form['treatment'])
    rounds = request.form['rounds']
    wholesale_price = request.form['wholesale_price']
    retail_price = request.form['retail_price']
    distributions = request.form.getlist('distributions[]')
    name = current_user.id + "_" + request.form['name']
    return redirect(url_for('add_distributions_parameters',
                            treatment=treatment, rounds=rounds,
                            wholesale_price=wholesale_price,
                            retail_price=retail_price,
                            distributions=distributions,
                            name=name))


@app.route('/admin/add_distribution_parameters', methods=['GET'])
@login_required
def add_distributions_parameters():
    treatment = int(request.args.get('treatment', None))
    rounds = int(request.args.get('rounds', None))
    wholesale_price = float(request.args.get('wholesale_price', None))
    retail_price = float(request.args.get('retail_price', None))
    distributions = request.args.getlist('distributions')
    name = str(request.args.get('name', None))
    length = len(distributions)
    print(distributions)
    return render_template('admin/add_distribution_parameters.html',
                           treatment=treatment, rounds=rounds,
                           wholesale_price=wholesale_price,
                           retail_price=retail_price,
                           distributions=distributions, length=length,
                           name=name, current_user=current_user)


@app.route('/admin/process_add_distribution_parameters', methods=['GET', 'POST'])
@login_required
def process_add_distributions_parameters():
    treatment = int(request.form['treatment'])
    rounds = int(request.form['rounds'])
    wholesale_price = float(request.form['wholesale_price'])
    retail_price = float(request.form['retail_price'])
    distributions = request.args.getlist('distributions')
    name = str(request.form['name'])
    length = len(distributions)
    parameters = []
    for i, distribution in enumerate(distributions, start=0):
        print(distribution)
        if distribution == 'Pool':
            pool = []
            show = int(request.form['show_' + str(i)])
            try:
                for number in request.form['sample_' + str(i)].split(','):
                    if int(number) < 0:
                        flash('Invalid input for sample pool')
                        return redirect(url_for('add_distributions_parameters',
                                                treatment=treatment, rounds=rounds,
                                                wholesale_price=wholesale_price,
                                                retail_price=retail_price,
                                                distributions=distributions, length=length,
                                                name=name, current_user=current_user))
                    pool.append(int(number))
            except:
                flash('Invalid input for sample pool')
                return redirect(url_for('add_distributions_parameters',
                                        treatment=treatment, rounds=rounds,
                                        wholesale_price=wholesale_price,
                                        retail_price=retail_price,
                                        distributions=distributions, length=length,
                                        name=name, current_user=current_user))
            parameters.append(
                {
                    distribution:
                        {
                            'sample': pool,
                            'show': show
                        }
                }
            )
        elif distribution == 'Normal':
            parameters.append({
                distribution: {
                    'mean': int(request.form['mean_' + str(i)]),
                    'standard_deviation': int(request.form['standard_deviation_' + str(i)])
                }
            })
        elif distribution == 'Triangular':
            if not (int(request.form['lower_bound_' + str(i)])
                    < int(request.form['peak_' + str(i)])
                    < int(request.form['upper_bound_' + str(i)])):
                flash('Incorrect values for triangular distributions '
                      '(lower bound < peak < upper bound was not fulfilled)')
                return redirect(url_for('add_distributions_parameters',
                                        treatment=treatment, rounds=rounds,
                                        wholesale_price=wholesale_price,
                                        retail_price=retail_price,
                                        distributions=distributions, length=length,
                                        name=name, current_user=current_user))
            parameters.append({
                distribution: {
                    'lower_bound': int(request.form['lower_bound_' + str(i)]),
                    'upper_bound': int(request.form['upper_bound_' + str(i)]),
                    'peak': int(request.form['peak_' + str(i)])
                }
            })
        elif distribution == 'Uniform':
            if not (int(request.form['lower_bound_' + str(i)])
                    < int(request.form['upper_bound_' + str(i)])):
                flash('Incorrect values for uniform distributions '
                      '(lower bound < upper bound was not fulfilled)')
                return redirect(url_for('add_distributions_parameters',
                                        treatment=treatment, rounds=rounds,
                                        wholesale_price=wholesale_price,
                                        retail_price=retail_price,
                                        distributions=distributions, length=length,
                                        name=name, current_user=current_user))
            parameters.append({
                distribution: {
                    'lower_bound': int(request.form['lower_bound_' + str(i)]),
                    'upper_bound': int(request.form['upper_bound_' + str(i)])
                }
            })

    dumping = {
        'treatment': treatment,
        'rounds': rounds,
        'wholesale_price': wholesale_price,
        'retail_price': retail_price,
        'parameters': parameters
    }
    dest = name + '.json'
    with open(dest, 'w') as outfile:
        outfile.write('')
        json.dump(dumping, outfile)

    shutil.move(os.getcwd() + '/' + dest, os.getcwd() + '/app/distributions/' + dest)
    flash('The detail ' + name + ' has been successfully created')
    return redirect(url_for('admin_home'))
