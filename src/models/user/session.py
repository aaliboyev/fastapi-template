import typing
from datetime import datetime

from sqlmodel import Field, Relationship

from src.lib.generators import generate_token
from src.models.base import BaseModelWithTimestamp

if typing.TYPE_CHECKING:
    from src.models.user import User


class UserSession(BaseModelWithTimestamp, table=True):
    __tablename__ = "user_sessions"

    token: str = Field(default_factory=generate_token)
    ip: str | None = None
    expiration: datetime
    user_agent: str | None = None

    user_id: int = Field(default=None, foreign_key="users.id")
    user: "User" = Relationship(
        back_populates="session", sa_relationship_kwargs={"lazy": "joined"}
    )
