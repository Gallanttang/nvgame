def get_day_index(current_user, game):
    day_index = len(game.query.filter_by(id=current_user.id).all()) + 1


def get_current_parameters(current_user, parameters):
    current_par = parameters.query.filter_by(scode=current_user.student_number).all()[-1]


def get_current_demand(current_user, demand):
    current_demand = demand.query.filter_by(scode=current_user.student_number).all()[-1]
