from typing import TypeVar

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from src.lib.exceptions.rbac import RequiresPermission
from src.schema.user import UserBase

from ..base import BaseModelWithSoftDelete
from .account import UserAccount
from .permission import Permission
from .role import Role, UserRole
from .session import UserSession

UserModel = TypeVar("UserModel", bound="User")


class UserPermission(SQLModel, table=True):
    __tablename__ = "user_permissions"
    user_id: int | None = Field(default=None, foreign_key="users.id", primary_key=True)
    permission_id: int | None = Field(
        default=None, foreign_key="permissions.id", primary_key=True
    )


class User(BaseModelWithSoftDelete, UserBase, table=True):
    """
    User model with authentication and authorization.

    Relationships (roles and permissions) are eagerly loaded via lazy="joined"
    so permission checking methods work on already-loaded data.
    """

    __tablename__ = "users"

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    email_verified: bool = False
    hashed_password: str = Field()
    is_active: bool = True
    is_superuser: bool = False

    # Relationships - eagerly loaded for permission checks
    session: "UserSession" = Relationship(back_populates="user")
    roles: list["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,
        sa_relationship_kwargs={"lazy": "joined"},
    )
    permissions: list["Permission"] = Relationship(
        link_model=UserPermission, sa_relationship_kwargs={"lazy": "joined"}
    )
    accounts: list["UserAccount"] = Relationship(back_populates="user")

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def can(self, permission: str) -> None:
        """
        Check if user has permission, raise exception if not.

        Superusers have all permissions.

        Args:
            permission: Permission name to check

        Raises:
            RequiresPermission: If user lacks the permission
        """
        if self.is_superuser:
            return None
        if not self.has_permission(permission):
            raise RequiresPermission(permission)
        return None

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Checks both direct user permissions and permissions via roles.

        Args:
            permission: Permission name to check

        Returns:
            True if user has the permission, False otherwise
        """
        has_perm = False
        if self.permissions:
            has_perm = any(permission == p.name for p in self.permissions)
        if self.roles:
            has_perm = has_perm or any(
                role.has_permission(permission) for role in self.roles
            )
        return has_perm

    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            role_name: Role name to check

        Returns:
            True if user has the role, False otherwise
        """
        if not self.roles:
            return False
        return any(role.name == role_name for role in self.roles)
