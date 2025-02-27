import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv("DB_URL")

engine = create_async_engine(
    DATABASE_URL, future=True, pool_size=20, max_overflow=10, pool_timeout=30
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """
    Initialize the database by creating the tables from the Base metadata.
    This function is typically called once when the application starts.
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
