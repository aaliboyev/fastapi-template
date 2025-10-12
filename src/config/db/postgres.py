import logging

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import settings

logger = logging.getLogger("sqlalchemy.engine")

# When debugging db queries and sqlalchemy, set this to higher value to see query logs.
logger.setLevel(logging.NOTSET)


engine = create_engine(str(settings.sqlalchemy_url))
async_engine = create_async_engine(str(settings.sqlalchemy_url))

make_async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

__all__ = [
    "AsyncSession",
    "Session",
    "make_async_session",
    "async_engine",
    "engine",
]
