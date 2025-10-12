from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel import Session, SQLModel, func, select

from src.config.db import AsyncSession
from src.lib.abstracts import BaseService, BaseServiceProvider
from src.models.base import BaseModelWithSoftDelete


class BaseServiceProviderWithDB(BaseServiceProvider):
    session: Session | None = None

    def __init__(self, service, *args, **kwargs):
        self.session = kwargs.pop("session", None)
        super().__init__(service, *args, **kwargs)


class BaseServiceWithDB(BaseService):
    session: Session | None = None
    model_class: type[SQLModel]

    def __init__(self, session: Session | None = None, *args, **kwargs):
        self.session = session

    @classmethod
    def _supports_soft_delete(cls) -> bool:
        """Check if the model class supports soft delete functionality."""
        return issubclass(cls.model_class, BaseModelWithSoftDelete)

    @classmethod
    def get(
        cls, model_id: int, session: Session, with_deleted=False
    ) -> SQLModel | None:
        """Get a single model instance by ID."""
        statement = select(cls.model_class).where(cls.model_class.id == model_id)  # type: ignore[attr-defined]

        # Only filter deleted records if model supports soft delete
        if cls._supports_soft_delete() and not with_deleted:
            statement = statement.where(cls.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]

        return session.exec(statement).first()

    @classmethod
    def list(
        cls, session: Session, statement=None, include_deleted=False
    ) -> Sequence[SQLModel]:
        """List all model instances matching the query."""
        return session.exec(
            cls.list_query(statement=statement, include_deleted=include_deleted)
        ).all()

    @classmethod
    def list_query(cls, statement=None, include_deleted=False):
        """Build a query for listing model instances."""
        if statement is None:
            statement = select(cls.model_class)

        # Only filter deleted records if model supports soft delete
        if cls._supports_soft_delete() and not include_deleted:
            statement = statement.where(cls.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]

        return statement

    @classmethod
    def delete(cls, instance: SQLModel, session: Session, soft=True) -> None:
        """
        Delete a model instance.

        Args:
            instance: The model instance to delete
            session: Database session
            soft: If True and model supports soft delete, perform soft delete.
                  Otherwise perform hard delete.
        """
        if soft and cls._supports_soft_delete():
            # Soft delete by setting deleted_at timestamp
            instance.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
            session.add(instance)
            session.commit()
            session.refresh(instance)
        else:
            # Hard delete from database
            session.delete(instance)
            session.commit()

    @classmethod
    def count(cls, session: Session, include_deleted=False) -> int:
        """Count the number of model instances."""
        statement = select(func.count()).select_from(cls.model_class)

        # Only filter deleted records if model supports soft delete
        if cls._supports_soft_delete() and not include_deleted:
            statement = statement.where(cls.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]

        return session.exec(statement).one()


class BaseAsyncServiceWithDB(BaseService):
    """
    Async base service for database operations.

    This is the preferred base class for all services. Use async/await patterns
    for all database operations. For rare cases requiring sync operations,
    use BaseServiceWithDB instead.
    """

    session: AsyncSession | None = None
    model_class: type[SQLModel]

    def __init__(self, session: AsyncSession | None = None, *args, **kwargs):
        self.session = session

    @classmethod
    def _supports_soft_delete(cls) -> bool:
        """Check if the model class supports soft delete functionality."""
        return issubclass(cls.model_class, BaseModelWithSoftDelete)

    @classmethod
    async def get(
        cls, model_id: int, session: AsyncSession, with_deleted=False
    ) -> SQLModel | None:
        """Get a single model instance by ID."""
        statement = select(cls.model_class).where(cls.model_class.id == model_id)  # type: ignore[attr-defined]

        # Only filter deleted records if model supports soft delete
        if cls._supports_soft_delete() and not with_deleted:
            statement = statement.where(cls.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]

        result = await session.exec(statement)
        return result.one_or_none()

    @classmethod
    async def list(
        cls, session: AsyncSession, statement=None, include_deleted=False
    ) -> Sequence[SQLModel]:
        """List all model instances matching the query."""
        query = cls.list_query(statement=statement, include_deleted=include_deleted)
        result = await session.exec(query)
        return result.all()

    @classmethod
    def list_query(cls, statement=None, include_deleted=False):
        """Build a query for listing model instances."""
        if statement is None:
            statement = select(cls.model_class)

        # Only filter deleted records if model supports soft delete
        if cls._supports_soft_delete() and not include_deleted:
            statement = statement.where(cls.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]

        return statement

    @classmethod
    async def delete(cls, instance: SQLModel, session: AsyncSession, soft=True) -> None:
        """
        Delete a model instance.

        Args:
            instance: The model instance to delete
            session: Async database session
            soft: If True and model supports soft delete, perform soft delete.
                  Otherwise perform hard delete.
        """
        if soft and cls._supports_soft_delete():
            # Soft delete by setting deleted_at timestamp
            instance.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
        else:
            # Hard delete from database
            await session.delete(instance)
            await session.commit()

    @classmethod
    async def count(cls, session: AsyncSession, include_deleted=False) -> int:
        """Count the number of model instances."""
        statement = select(func.count()).select_from(cls.model_class)

        # Only filter deleted records if model supports soft delete
        if cls._supports_soft_delete() and not include_deleted:
            statement = statement.where(cls.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]

        result = await session.exec(statement)
        return result.one()
