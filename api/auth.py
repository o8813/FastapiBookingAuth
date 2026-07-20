from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from database.models import User, UserRefresh
from database.schemas import UserInputSchema, UserLoginSchema, UserOutSchema
from fastapi import HTTPException, APIRouter, status, Depends
from passlib.context import CryptContext
from config import config
from jose import jwt
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
import uuid

router = APIRouter(prefix='/auth', tags=['Auth'])

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def created_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expiration_time = datetime.now(timezone.utc) + expires_delta
    to_encode.update({
        "exp": expiration_time,
        "jti": str(uuid.uuid4()), # Уникальный ID токена
    })
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

def create_access_token(user_id: int) -> str:
    return created_token(
        {
            'sub': str(user_id),
            'id': user_id,            # Ожидается приемником ("Token has no id")
            'user_id': user_id,       # Запасной вариант для дефолтного USER_ID_CLAIM
            'token_type': 'access',   # Ожидается SimpleJWT вместо 'type'
        },
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_LIFETIME)
    )

def create_refresh_token(user_id: int) -> str:
    return created_token(
        {
            'sub': str(user_id),
            'id': user_id,
            'user_id': user_id,
            'token_type': 'refresh',
        },
        expires_delta=timedelta(days=config.REFRESH_TOKEN_LIFETIME)
    )

@router.post('/register', response_model=dict, tags=['Auth'])
async def register(schema: UserInputSchema, db: AsyncSession = Depends(get_db)):
    username = select(User).where(User.username==schema.username)
    username_res = await db.execute(username)
    username_scal = username_res.scalar_one_or_none()

    if username_scal:
        raise HTTPException(detail='This username is already taken', status_code=status.HTTP_409_CONFLICT)

    email = select(User).where(User.email==schema.email)
    email_res = await db.execute(email)
    email_scal = email_res.scalar_one_or_none()

    if email_scal:
        raise HTTPException(detail='This email is already taken', status_code=status.HTTP_409_CONFLICT)

    update_data = schema.model_dump()
    update_data['password'] = hash_password(schema.password)
    user = User(**update_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    refresh = UserRefresh(user_id=user.id, token=refresh_token)
    db.add(refresh)
    await db.commit()
    await db.refresh(refresh)

    return {
        'detail': 'Successfully registered',
        'refresh': refresh_token,
        'access': access_token,
        'token-type': 'Bearer'
    }

@router.post('/login', response_model=dict, tags=['Auth'])
async def login(schema: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.username==schema.username)
    result = await db.execute(query)
    scal = result.scalar_one_or_none()

    if not scal or not verify_password(schema.password, scal.password):
        raise HTTPException(detail='Invalid credentials', status_code=status.HTTP_400_BAD_REQUEST)

    access_token = create_access_token(scal.id)
    refresh_token = create_refresh_token(scal.id)
    refresh = UserRefresh(user_id=scal.id, token=refresh_token)

    db.add(refresh)
    await db.commit()
    await db.refresh(refresh)
    return {
        'detail': 'Successfully logged in',
        'refresh': refresh_token,
        'access': access_token,
        'token-type': 'Bearer'
    }

@router.post('/logout', response_model=dict, tags=['Auth'])
async def logout(refresh_token: str, db: AsyncSession = Depends(get_db)):
    query = select(UserRefresh).where(UserRefresh.token==refresh_token)
    result = await db.execute(query)
    scal = result.scalar_one_or_none()

    if not scal:
        raise HTTPException(detail='Invalid token', status_code=status.HTTP_400_BAD_REQUEST)

    await db.delete(scal)
    await db.commit()
    return {
        'detail': 'Successfully logged out'
    }

@router.post('/access', response_model=dict, tags=['Auth'])
async def access(refresh_token: str, db: AsyncSession = Depends(get_db)):
    query = select(UserRefresh).where(UserRefresh.token==refresh_token)
    result = await db.execute(query)
    scal = result.scalar_one_or_none()

    if not scal:
        raise HTTPException(detail='Invalid token', status_code=status.HTTP_400_BAD_REQUEST)

    access_token = create_access_token(scal.user_id)
    return {
        'access': access_token,
        'token-type': 'Bearer'
    }