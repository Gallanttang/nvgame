from app import db
from app import loginManager
from flask_login import UserMixin
import scipy.stats as stats
import numpy as np
import enum


class User(UserMixin, db.Model):
    id = db.Column(db.String(), primary_key=True)
    student_number = db.Column(db.Integer, nullable=False)
    session_code = db.Column(db.String(), nullable=False)
    pref_name = db.Column(db.String(), nullable=False)

    __table_args__ = (
        db.CheckConstraint('10000000 <= self.student_number'),
        db.CheckConstraint('self.student_number < 100000000'),
    )

    def __repr__(self):
        return '<Student {}>'.format(self.id)


@loginManager.user_loader
def load_user(student_number):
    return User.query.get(int(student_number))


# enum class for distribution type
class DistributionType(enum.Enum):
    SAMPLE_POOL = 'Sample Pool'
    NORMAL = 'Normal Distribution'
    TRIANGULAR = 'Triangular Distibution'
    UNIFORM = 'Uniform Distibution'


# default function for scode in Demand model
def default_scode():
    try:
        recent_added_par = Parameter.query.all()[-1]
    except:
        return 'Nothing in parameters table!'
    try:
        ins_name = recent_added_par.scode.split('_')[0]
        ins_code = recent_added_par.scode.split('_')[1]
        assert ins_name in ['harishk', 'timh']
        assert len(ins_code) == 2
        assert int(ins_code) > 0
        assert int(ins_code) < 100
        assert recent_added_par.retail_price > recent_added_par.wholesale_price
        return recent_added_par.scode
    except:
        return 'Invaild session code or prices!'


# default function for demand_past in Demand model
def default_demand_past():
    try:
        recent_added_par = Parameter.query.all()[-1]
    except:
        return 'Nothing in parameters table!'
    if recent_added_par.demand_pattern == DistributionType.SAMPLE_POOL:
        try:
            with open(recent_added_par.sample_pool_input_file_name_txt) as input_file:
                sample_all_past_str = input_file.read()
                sample_all_past_list = [int(x.strip()) for x in sample_all_past_str.split(',') if x.strip()]
                assert len(
                    sample_all_past_list) >= recent_added_par.sample_pool_number_of_past_demand_show \
                       + recent_added_par.nrounds
                sample_past_list = sample_all_past_list[0:recent_added_par.sample_pool_number_of_past_demand_show]
                sample_past = str(sample_past_list)[1:-1]
            return sample_past
        except:
            return 'Invalid sample pool input txt file!'
    else:
        return 'N/A'


# default function for demand_new in Demand model
def default_demand_new():
    try:
        recent_added_par = Parameter.query.all()[-1]
    except:
        return 'Nothing in parameters table!'
    if recent_added_par.demand_pattern == DistributionType.SAMPLE_POOL:
        try:
            with open(recent_added_par.sample_pool_input_file_name_txt) as input_file:
                sample_all_new_str = input_file.read()
                sample_all_new_list = [int(x.strip()) for x in sample_all_new_str.split(',') if x.strip()]
                assert len(
                    sample_all_new_list) >= recent_added_par.sample_pool_number_of_past_demand_show + recent_added_par.nrounds
                sample_new_list = sample_all_new_list[
                                  recent_added_par.sample_pool_number_of_past_demand_show:recent_added_par.sample_pool_number_of_past_demand_show + recent_added_par.nrounds]
                sample_new = str(sample_new_list)[1:-1]
            return sample_new
        except:
            return 'Invaild sample pool input txt file!'
    else:
        if recent_added_par.demand_pattern == DistributionType.NORMAL:
            try:
                assert recent_added_par.distribution_all_upper_bound > recent_added_par.distribution_all_lower_bound
                mu = recent_added_par.distribution_normal_mean
                assert mu > recent_added_par.distribution_all_lower_bound
                assert mu < recent_added_par.distribution_all_upper_bound
                sigma = recent_added_par.distribution_normal_std
                rvs_normal = stats.truncnorm((recent_added_par.distribution_all_lower_bound - mu) / sigma,
                                             (recent_added_par.distribution_all_upper_bound - mu) / sigma, loc=mu,
                                             scale=sigma)
                generated_normal = rvs_normal.rvs(recent_added_par.nrounds)
                return str([int(round(x)) for x in generated_normal])[1:-1]
            except:
                return 'Invalid parameters for normal distribution!'
        elif recent_added_par.demand_pattern == DistributionType.TRIANGULAR:
            try:
                assert recent_added_par.distribution_all_upper_bound > recent_added_par.distribution_all_lower_bound
                assert recent_added_par.distribution_triangular_peak > recent_added_par.distribution_all_lower_bound
                assert recent_added_par.distribution_triangular_peak < recent_added_par.distribution_all_upper_bound
                generated_triangular = np.random.triangular(recent_added_par.distribution_all_lower_bound,
                                                            recent_added_par.distribution_triangular_peak,
                                                            recent_added_par.distribution_all_upper_bound,
                                                            recent_added_par.nrounds)
                return str([int(round(x)) for x in generated_triangular])[1:-1]
            except:
                return 'Invalid parameters for triangular distribution!'
        else:  # recent_added_par.demand_pattern == DistributionType.UNIFORM
            try:
                assert recent_added_par.distribution_all_upper_bound > recent_added_par.distribution_all_lower_bound
                generated_uniform = np.random.randint(recent_added_par.distribution_all_lower_bound,
                                                      recent_added_par.distribution_all_upper_bound,
                                                      recent_added_par.nrounds)
                return str([int(round(x)) for x in generated_uniform])[1:-1]
            except:
                return 'Invalid parameters for uniform distribution!'


# deafult function for scode in Pace model
def default_pace_scode():
    try:
        recent_added_par_pace = Parameter.query.all()[-1]
        assert Demand.query.filter_by(scode=recent_added_par_pace.scode).all()
    except:
        return 'Complete Parameter or Demand table first!'
    if recent_added_par_pace.consistent_pace:
        return recent_added_par_pace.scode
    else:
        return 'This is not a consistent pace session!'


# default function for default_session_size in Pace model
def default_session_size():
    try:
        recent_added_par_pace = Parameter.query.all()[-1]
        assert Demand.query.filter_by(scode=recent_added_par_pace.scode).all()
        recent_added_user_count_pace = len(User.query.filter_by(scode=recent_added_par_pace.scode).all())
    except:
        return 'Complete Parameter or Demand table first!'
    if recent_added_par_pace.consistent_pace:
        return recent_added_user_count_pace
    else:
        return 'This is not a consistent pace session!'


# default function for default_session_id_collection in Pace model
def default_session_id_collection():
    try:
        recent_added_par_pace = Parameter.query.all()[-1]
        assert Demand.query.filter_by(scode=recent_added_par_pace.scode).all()
        recent_added_user_collection_pace = [x[0] for x in User.query.with_entities(User.id).filter_by(
            scode=recent_added_par_pace.scode).all()]
    except:
        return 'Complete Parameter or Demand table first!'
    if recent_added_par_pace.consistent_pace:
        return str(recent_added_user_collection_pace)[1:-1]
    else:
        return 'This is not a consistent pace session!'


# model 2: parameter - game setup
class Parameter(db.Model):
    par_id = db.Column(db.Integer, primary_key=True)
    scode = db.Column(db.String(10), nullable=False, unique=True)
    consistent_pace = db.Column(db.Boolean, nullable=False, default=False)
    nrounds = db.Column(db.Integer, default=10, nullable=False)
    wholesale_price = db.Column(db.Float, default=1, nullable=False)
    retail_price = db.Column(db.Float, default=4, nullable=False)
    demand_pattern = db.Column(db.Enum(DistributionType), nullable=False)
    sample_pool_input_file_name_txt = db.Column(db.String(50))
    sample_pool_number_of_past_demand_show = db.Column(db.Integer)
    distribution_all_lower_bound = db.Column(db.Integer)
    distribution_all_upper_bound = db.Column(db.Integer)
    distribution_normal_mean = db.Column(db.Float)
    distribution_normal_std = db.Column(db.Float)
    distribution_triangular_peak = db.Column(db.Float)

    __table_args__ = (
        db.CheckConstraint('parameter.nrounds >= 10'),
        db.CheckConstraint('parameter.nrounds <= 50'),
        db.CheckConstraint('parameter.wholesale_price >= 0'),
        db.CheckConstraint('parameter.retail_price > 0'),
        db.CheckConstraint('parameter.sample_pool_number_of_past_demand_show >= 0'),
        db.CheckConstraint('parameter.distribution_all_lower_bound >= 0'),
        db.CheckConstraint('parameter.distribution_all_upper_bound > 0'),
        db.CheckConstraint('parameter.distribution_normal_mean > 0'),
        db.CheckConstraint('parameter.distribution_normal_std > 0'),
        db.CheckConstraint('parameter.distribution_triangular_peak > 0'))


# model 3 demand - generated demand amount for each round
class Demand(db.Model):
    demand_id = db.Column(db.Integer, primary_key=True)
    scode = db.Column(db.String(10), nullable=False, default=default_scode, unique=True)
    demand_past = db.Column(db.String(300), nullable=False, default=default_demand_past)
    demand_new = db.Column(db.String(300), nullable=False, default=default_demand_new)


# model 4 game - game record
class Game(db.Model):
    record_id = db.Column(db.Integer, primary_key=True)
    scode = db.Column(db.String(10), nullable=False)
    id = db.Column(db.Integer, nullable=False)
    pname = db.Column(db.String(25), nullable=False)
    day_index = db.Column(db.Integer, nullable=False)
    norder = db.Column(db.Integer, nullable=False)
    ndemand = db.Column(db.Integer, nullable=False)
    nsold = db.Column(db.Integer, nullable=False)
    nlost = db.Column(db.Integer, nullable=False)
    rev = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    total_profit = db.Column(db.Float, nullable=False)
    round_rank = db.Column(db.Integer, default=-1, nullable=False)
    total_rank = db.Column(db.Integer, default=-1, nullable=False)


# model 5 pace - record information for consistent pace game sessions
class Pace(db.Model):
    demand_id = db.Column(db.Integer, primary_key=True)
    scode = db.Column(db.String(10), nullable=False, default=default_pace_scode, unique=True)
    session_size = db.Column(db.Integer, nullable=False, default=default_session_size)
    session_id_collection = db.Column(db.String(3000), nullable=False, default=default_session_id_collection())



