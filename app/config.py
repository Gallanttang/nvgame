class Config(object):
    SECRET_KEY = 'newsvendor_secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///newsvendor_db.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
