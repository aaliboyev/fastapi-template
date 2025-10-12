from sqlmodel import Field

from src.models.base import BaseModel


class Permission(BaseModel, table=True):
    __tablename__ = "permissions"

    name: str = Field(unique=True)
    title: str
    description: str | None = None
