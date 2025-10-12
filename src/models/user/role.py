import typing

from sqlmodel import Field, Relationship, SQLModel

from ..base import BaseModel
from .permission import Permission

if typing.TYPE_CHECKING:
    from src.models.user import User


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: int | None = Field(default=None, foreign_key="roles.id", primary_key=True)
    permission_id: int | None = Field(
        default=None, foreign_key="permissions.id", primary_key=True
    )


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    user_id: int | None = Field(default=None, foreign_key="users.id", primary_key=True)
    role_id: int | None = Field(default=None, foreign_key="roles.id", primary_key=True)


class Role(BaseModel, table=True):
    """
    Role model for role-based access control (RBAC).

    Permissions are eagerly loaded via lazy="joined" so permission checks
    work on already-loaded data without additional queries.
    """

    __tablename__ = "roles"

    name: str = Field(unique=True)
    title: str
    description: str | None = None

    users: list["User"] = Relationship(back_populates="roles", link_model=UserRole)
    permissions: list["Permission"] = Relationship(
        link_model=RolePermission, sa_relationship_kwargs={"lazy": "joined"}
    )

    def has_permission(self, permission: int | str) -> bool:
        """
        Check if role has a specific permission.

        Args:
            permission: Permission ID or name to check

        Returns:
            True if role has the permission, False otherwise
        """
        if not self.permissions:
            return False

        if isinstance(permission, int):
            return any(permission == p.id for p in self.permissions)
        return any(permission == p.name for p in self.permissions)
