from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import config
from sqlalchemy.orm import DeclarativeBase

async_engine = create_async_engine(config.DATABASE_URL, echo=True)
async_session = async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

class Base(DeclarativeBase):
    pass