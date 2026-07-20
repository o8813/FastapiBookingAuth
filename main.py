from fastapi import FastAPI
from admin.setup import admin_setup
import uvicorn
from api import auth, profile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='Booking Auth')
app.include_router(auth.router)
app.include_router(profile.router)

admin_setup(app)

origins = [
    'http://localhost',
    'http://localhost:3000',
    'http://frontend'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)