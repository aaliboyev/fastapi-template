from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Field, Session, SQLModel, func, select


class HasDeletedAt(Protocol):
    """Protocol for models that support soft delete."""

    deleted_at: datetime | None


class BaseModel(SQLModel):
    id: int = Field(default=None, primary_key=True)

    @classmethod
    def count(cls, session: Session) -> int:
        return session.exec(select(func.count()).select_from(cls)).one()


class BaseModelWithTimestamp(BaseModel):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[call-overload]
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=TIMESTAMP(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
    )


class BaseModelWithSoftDelete(BaseModelWithTimestamp):
    deleted_at: datetime | None = Field(default=None, sa_type=TIMESTAMP(timezone=True))  # type: ignore[call-overload]
