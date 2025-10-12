from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from src.models.base import BaseModelWithTimestamp


class UserSetting(BaseModelWithTimestamp, table=True):
    """Database model for user settings"""

    __tablename__ = "user_settings"

    user_id: int = Field(foreign_key="users.id")
    data: dict = Field(default_factory=dict, sa_type=JSONB)
    name: str = Field(nullable=False)
    meta: dict = Field(default_factory=dict, sa_type=JSONB, nullable=True)
