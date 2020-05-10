import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'newsvendor_secret'
    FLASK_APP = '../main.py'
    DATABASE_FILE = 'nvgame.sqlite'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////' + os.path.join(basedir, DATABASE_FILE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # # error notification
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


class DevConfig(Config):
    FLASK_DEBUG = True
    TESTING = True
    DATABASE_URI = os.environ.get('DEV_DATABASE_URI')
