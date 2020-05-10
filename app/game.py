def get_day_index(current_user, game):
    day_index = len(game.query.filter_by(id=current_user.id).all()) + 1
    return day_index


def get_current_parameters(current_user, parameters):
    current_par = parameters.query.filter_by(session_code=current_user.session_code).all()[-1]
    return current_par


def get_current_demand(current_user, demand):
    current_demand = demand.query.filter_by(session_code=current_user.session_code).all()[-1]
    return current_demand


def get_current_pace(current_user, pace):
    return pace.query.filter_by(session_code=current_user.scode).all()[-1]
