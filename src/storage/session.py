from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.storage.database import AsyncSessionLocal


@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
