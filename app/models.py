from app import db
from app import loginManager
import datetime
from flask_login import UserMixin


# pre-set game modes for a game
class Details(db.Model):
    __tablename__ = 'Details'
    id = db.Column(db.String(20), primary_key=True)
    distribution_file = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(300), nullable=False)


# to store all users (student and admins)
class Users(db.Model, UserMixin):
    # change the id to only be the first 5 digits of sid and session coded
    __tablename__ = 'Users'
    # for students, first 5 characters are their student id
    id = db.Column(db.String(60), primary_key=True)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    name = db.Column(db.String(60), nullable=False)


# keeps a special record of who is an admin (has passwords too)
class Admins(db.Model):
    default_password = 'OpLogAdmins!'
    __tablename__ = 'Admins'
    id = db.Column(db.String(60), db.ForeignKey('Users.id'), primary_key=True)
    password = db.Column(db.String(12), default=default_password)
    active = db.Column(db.Boolean, default=True)


@loginManager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


class Parameters(db.Model):
    __tablename__ = 'Parameters'
    id = db.Column(db.String(16), primary_key=True)
    admin = db.Column(db.String(60), db.ForeignKey(Admins.id))
    is_pace = db.Column(db.Boolean, nullable=False)
    detail_id = db.Column(db.Integer, db.ForeignKey(Details.id), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    start_time = db.Column(db.DateTime, nullable=True)
    ongoing = db.Column(db.Boolean, default=True)


class Results(db.Model):
    # add a column to calculate how long it took to answer the question
    __tablename__ = 'Results'
    id = db.Column(db.Integer, primary_key=True)
    parameter_id = db.Column(db.String(16), db.ForeignKey('Parameters.id'), nullable=False)
    user_id = db.Column(db.String(14), db.ForeignKey('Users.id'))
    round = db.Column(db.Integer, nullable=False)
    distribution = db.Column(db.String(50), nullable=False)
    demanded = db.Column(db.Integer, nullable=True)
    ordered = db.Column(db.Integer, nullable=True)
    time_start = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    time_answered = db.Column(db.DateTime, nullable=True)
