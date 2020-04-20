from app import app
from app import models
from app import db
from flask_admin import Admin, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_login import current_user
import os

# Initialize Admin Page
admin = Admin(app, name='Instructor Page')
# List of allowable users on admin page
adminIDs = [10000001100, 10000002200, 10000003300]


class MemoView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/memo.html')

    def is_accessible(self):
        try:
            return current_user.student_number in adminIDs
        except:
            return False


admin.add_view(MemoView(name='Memo'))


class ParameterView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_filters = ['scode']

    def is_accessible(self):
        try:
            return current_user.student_number in adminIDs
        except:
            return False


admin.add_view(ParameterView(models.Parameter, db.session))


class MyFileAdmin(FileAdmin):
    def is_accessible(self):
        try:
            return current_user.student_number in adminIDs
        except:
            return False


admin.add_view(MyFileAdmin(os.getcwd(), name='Files'))


class DemandView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_filters = ['scode']

    def is_accessible(self):
        try:
            return current_user.student_number in adminIDs
        except:
            return False


admin.add_view(DemandView(models.Demand, db.session))


class PaceView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_filters = ['scode']

    def is_accessible(self):
        try:
            return current_user.id in adminIDs
        except:
            return False


admin.add_view(PaceView(models.Pace, db.session))


class UserView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_filters = ['id', 'student_number', 'session_code']

    def is_accessible(self):
        try:
            return current_user.id in adminIDs
        except:
            return False


admin.add_view(UserView(models.User, db.session))


class GameView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_filters = ['record_id', 'scode', 'id', 'pname', 'day_index',
                      'norder', 'ndemand', 'nsold', 'nlost',
                      'rev', 'cost', 'profit', 'total_profit']

    def is_accessible(self):
        try:
            return current_user.id in adminIDs
        except:
            return False


admin.add_view(GameView(models.Game, db.session))
