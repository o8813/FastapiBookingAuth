from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserRefresh
from database.schemas import UserOutSchema, UserUpdateSchema, UserRefreshSchema
from fastapi import status, HTTPException, APIRouter, Depends
from database.connection import get_db
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from jose import jwt, JWTError
from config import config

router = APIRouter(prefix='/profile', tags=['Profile'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        subject = payload['sub']
        if subject is None:
            raise credentials_exception
        user_id = int(subject)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    query = select(User).where(User.id==user_id)
    result = await db.execute(query)
    scal = result.scalar_one_or_none()

    if not scal:
        raise credentials_exception
    return scal

@router.get('/', response_model=UserOutSchema, tags=['Profile'])
async def get(current_user: User = Depends(get_current_user)):
    return current_user

@router.put('/{user_id}/', response_model=UserOutSchema, tags=['Profile'])
async def put(
        user_id: int,
        schema: UserUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id==user_id))
    scal = result.scalar_one_or_none()

    if not scal:
        raise HTTPException(detail=f'No user with id {user_id}', status_code=status.HTTP_404_NOT_FOUND)

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scal, key, value)

    await db.commit()
    await db.refresh(scal)
    return scal

@router.delete('/', response_model=dict, tags=['Profile'])
async def delete(schema: UserRefreshSchema, db: AsyncSession = Depends(get_db)):
    query = (
        select(User)
        .join(UserRefresh, User.id == UserRefresh.user_id)
        .where(UserRefresh.token == schema.refresh_token)
    )
    result = await db.execute(query)
    scal = result.scalar_one_or_none()

    if not scal:
        raise HTTPException(detail='Invalid token', status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(scal)
    await db.commit()
    return {'detail': 'Account has been deleted'}