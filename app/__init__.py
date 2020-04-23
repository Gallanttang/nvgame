from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from app import config


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(obj=config.DevConfig)
loginManager = LoginManager(app)
loginManager.login_view = 'signin.html'
db = SQLAlchemy()

from app import models

with app.app_context():
    db.init_app(app=app)
    db.create_all(app=app)
    migrate = Migrate(app=app, db=db)

from app import routes


