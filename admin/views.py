from sqladmin import ModelView
from database.models import *

class UserAdmin(ModelView, model=User):
    column_list = '__all__'

class UserRefreshAdmin(ModelView, model=UserRefresh):
    column_list = '__all__'