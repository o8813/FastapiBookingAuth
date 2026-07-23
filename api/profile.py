from typing import Annotated

from config import config
from database.connection import get_db
from database.models import User, UserRefresh
from database.schemas import UserOutSchema, UserUpdateSchema
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/profile', tags=['Profile'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        subject = payload.get('user_id') or payload.get('sub')
        if subject is None:
            raise credentials_exception
        user_id = int(subject)

    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    refresh_check = await db.execute(
        select(UserRefresh).where(UserRefresh.user_id == user.id)
    )
    if not refresh_check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Session has been closed (logged out)',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    return user

@router.get('/', response_model=UserOutSchema, tags=['Profile'])
async def get(current_user: User = Depends(get_current_user)):
    return current_user

@router.put('/', response_model=UserOutSchema, tags=['Profile'])
async def put(
        schema: UserUpdateSchema,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    update_data = schema.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.delete('/', response_model=dict, tags=['Profile'])
async def delete(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    await db.delete(current_user)
    await db.commit()

    return {'detail': 'Account has been successfully deleted'}