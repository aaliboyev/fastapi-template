import typing
from datetime import datetime
from typing import Literal

from sqlalchemy.dialects.postgresql import JSONB, TEXT, VARCHAR
from sqlmodel import Field, Relationship

from src.models.base import BaseModelWithTimestamp

if typing.TYPE_CHECKING:
    from src.models.user import User

account_provider = Literal["gitlab", "github", "google", "credential"]


class UserAccount(BaseModelWithTimestamp, table=True):
    """
    User authentication account model.

    Stores OAuth tokens and credentials for various authentication providers.
    """

    __tablename__ = "user_accounts"

    account_id: str | None
    provider: account_provider = Field(sa_type=VARCHAR(30))  # type: ignore[call-overload]
    image: str | None = None
    access_token: str | None = Field(default=None, sa_type=TEXT)
    refresh_token: str | None = Field(default=None, sa_type=TEXT)
    access_token_expiration: datetime | None = None
    refresh_token_expiration: datetime | None = None
    access_scopes: str | None = None
    id_token: str | None = None
    password: str | None = None
    purpose: Literal["auth", "repo"] | None = Field(default="auth", sa_type=VARCHAR(20))  # type: ignore[call-overload]
    data: dict | None = Field(default=None, sa_type=JSONB)

    user_id: int = Field(default=None, foreign_key="users.id")
    user: "User" = Relationship(
        back_populates="accounts", sa_relationship_kwargs={"lazy": "joined"}
    )
