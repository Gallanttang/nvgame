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
    __tablename__ = 'Users'
    # for students, first 8 characters are their student id.
    # 9-14 characters indicates the session
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
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    start_time = db.Column(db.DateTime, nullable=True)
    ongoing = db.Column(db.Boolean, default=True)


class Results(db.Model):
    __tablename__ = 'Results'
    id = db.Column(db.Integer, primary_key=True)
    parameter_id = db.Column(db.String(16), db.ForeignKey(Parameters.id), nullable=False)
    user_id = db.Column(db.String(14), db.ForeignKey('Users.id'))
    round = db.Column(db.Integer, nullable=False)
