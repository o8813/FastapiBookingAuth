from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from database.schemas import UserOutSchema, UserUpdateSchema
from fastapi import status, HTTPException, APIRouter, Depends
from database.connection import get_db

router = APIRouter(prefix='/profile', tags=['Profile'])

@router.get('/{user_id}/', response_model=UserOutSchema, tags=['Profile'])
async def get(user_id: int, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.id==user_id)
    result = await db.execute(query)
    scal = result.scalar_one_or_none()

    if not scal:
        raise HTTPException(detail=f'No user with id {user_id}', status_code=status.HTTP_404_NOT_FOUND)
    return scal

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

@router.delete('/{user_id}/', response_model=dict, tags=['Profile'])
async def delete(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id==user_id))
    scal = result.scalar_one_or_none()

    if not scal:
        raise HTTPException(detail=f'No user with id {user_id}', status_code=status.HTTP_404_NOT_FOUND)

    await db.delete(scal)
    await db.commit()
    return {'detail': 'Account has been deleted'}