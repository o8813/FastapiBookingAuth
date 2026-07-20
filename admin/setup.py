from fastapi import FastAPI
from database.connection import async_engine
from sqladmin import Admin
from .views import *

def admin_setup(app: FastAPI):
    admin = Admin(app, async_engine)
    admin.add_view(UserAdmin)
    admin.add_view(UserRefreshAdmin)