from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

try:
    from core.config import settings
except ImportError as exc:
    raise ImportError(
        "Cannot import 'settings' from 'core.config'. Ensure the module exists and is correctly installed."
    ) from exc

engine = create_async_engine(settings.pg_dsn, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
