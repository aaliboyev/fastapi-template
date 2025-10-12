from collections.abc import AsyncGenerator, Generator
from typing import Annotated, TypeAlias

from fastapi import Depends

from src.config.db import AsyncSession, Session, engine, make_async_session


def get_db_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


async def get_async_db_session() -> AsyncGenerator[AsyncSession]:
    async with make_async_session() as session:
        yield session


DBSession: TypeAlias = Annotated[Session, Depends(get_db_session)]
AsyncDBSession: TypeAlias = Annotated[AsyncSession, Depends(get_async_db_session)]
