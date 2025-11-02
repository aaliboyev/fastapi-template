from datetime import UTC, datetime

from pydantic import EmailStr
from sqlmodel import select

from src.config.db import AsyncSession
from src.lib.security import get_password_hash, verify_password
from src.models.user import User, UserAccount, UserSession
from src.models.user.role import UserRole
from src.models.user.user import UserPermission
from src.schema.user import UserCreate, UserRegister, UserUpdate
from src.services.base import BaseAsyncServiceWithDB


class UserService(BaseAsyncServiceWithDB):
    """
    Async service for managing User database operations.

    All methods use async/await patterns with AsyncSession.
    """

    model_class = User

    @classmethod
    async def create(cls, user_in: UserCreate, session: AsyncSession) -> User:
        """
        Create a new user with hashed password.

        Args:
            user_in: User creation data
            session: Async database session

        Returns:
            Created user instance
        """
        user_data = user_in.model_dump(exclude={"password"})
        hashed_password = get_password_hash(user_in.password)

        db_user = User(**user_data, hashed_password=hashed_password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return db_user

    @classmethod
    async def register(cls, user_in: UserRegister, session: AsyncSession) -> User:
        """
        Register a new user (simplified create for public registration).

        Args:
            user_in: User registration data
            session: Async database session

        Returns:
            Created user instance
        """
        user_data = user_in.model_dump(exclude={"password"})
        hashed_password = get_password_hash(user_in.password)

        db_user = User(**user_data, hashed_password=hashed_password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return db_user

    @classmethod
    async def get_by_email(cls, email: EmailStr, session: AsyncSession) -> User | None:
        """
        Get user by email address.

        Args:
            email: User's email address
            session: Async database session

        Returns:
            User instance if found, None otherwise
        """
        statement = select(User).where(User.email == email)

        # Check if model supports soft delete
        if cls._supports_soft_delete():
            statement = statement.where(User.deleted_at.is_(None))  # type: ignore[union-attr]

        result = await session.exec(statement)
        return result.unique().one_or_none()

    @classmethod
    async def update(
        cls, db_user: User, user_in: UserUpdate, session: AsyncSession
    ) -> User:
        """
        Update user information.

        Handles password hashing if password is being updated.

        Args:
            db_user: Existing user instance
            user_in: Update data
            session: Async database session

        Returns:
            Updated user instance
        """
        user_data = user_in.model_dump(exclude_unset=True)
        extra_data = {}

        if "password" in user_data:
            password = user_data.pop("password")
            hashed_password = get_password_hash(password)
            extra_data["hashed_password"] = hashed_password

        db_user.sqlmodel_update(user_data, update=extra_data)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return db_user

    @classmethod
    async def update_password(
        cls,
        user: User,
        current_password: str,
        new_password: str,
        session: AsyncSession,
    ) -> User:
        """
        Update user password after verifying current password.

        Args:
            user: User instance
            current_password: Current password for verification
            new_password: New password to set
            session: Async database session

        Returns:
            Updated user instance

        Raises:
            ValueError: If current password is incorrect
        """
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    @classmethod
    async def add_role(cls, user: User, role_id: int, session: AsyncSession) -> User:
        """
        Add a role to user.

        Args:
            user: User instance
            role_id: ID of role to add
            session: Async database session

        Returns:
            User instance with updated roles
        """
        user_role = UserRole(user_id=user.id, role_id=role_id)
        session.add(user_role)
        await session.commit()
        await session.refresh(user)

        return user

    @classmethod
    async def remove_role(cls, user: User, role_id: int, session: AsyncSession) -> User:
        """
        Remove a role from user.

        Args:
            user: User instance
            role_id: ID of role to remove
            session: Async database session

        Returns:
            User instance with updated roles
        """
        statement = select(UserRole).where(
            UserRole.user_id == user.id, UserRole.role_id == role_id
        )
        result = await session.exec(statement)
        user_role = result.one()

        if user_role:
            await session.delete(user_role)
            await session.commit()
            await session.refresh(user)

        return user

    @classmethod
    async def add_permission(
        cls, user: User, permission_id: int, session: AsyncSession
    ) -> User:
        """
        Add a permission directly to user (not via role).

        Args:
            user: User instance
            permission_id: ID of permission to add
            session: Async database session

        Returns:
            User instance with updated permissions
        """
        user_permission = UserPermission(user_id=user.id, permission_id=permission_id)
        session.add(user_permission)
        await session.commit()
        await session.refresh(user)

        return user

    @classmethod
    async def remove_permission(
        cls, user: User, permission_id: int, session: AsyncSession
    ) -> User:
        """
        Remove a permission from user.

        Args:
            user: User instance
            permission_id: ID of permission to remove
            session: Async database session

        Returns:
            User instance with updated permissions
        """
        statement = select(UserPermission).where(
            UserPermission.user_id == user.id,
            UserPermission.permission_id == permission_id,
        )
        result = await session.exec(statement)
        user_permission = result.one()

        if user_permission:
            await session.delete(user_permission)
            await session.commit()
            await session.refresh(user)

        return user

    @classmethod
    async def authenticate(
        cls, email: EmailStr, password: str, session: AsyncSession
    ) -> User | None:
        """
        Authenticate user by email and password.

        Args:
            email: User's email
            password: Plain text password
            session: Async database session

        Returns:
            User instance if authentication successful, None otherwise
        """
        user = await cls.get_by_email(email, session)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    @classmethod
    async def logout(cls, session_id: str, session: AsyncSession):
        statement = select(UserSession).where(UserSession.token == session_id)
        result = await session.exec(statement)
        user_session = result.unique().one_or_none()

        if user_session:
            await session.delete(user_session)
            await session.commit()

    @classmethod
    async def get_by_session_token(
        cls, token: str, session: AsyncSession
    ) -> User | None:
        """
        Get user by session token.

        Queries the UserSession table by token and returns the associated user.

        Args:
            token: Session token (typically the session ID from cookies)
            session: Async database session

        Returns:
            User instance if session found and valid, None otherwise
        """

        statement = select(UserSession).where(
            UserSession.token == token, UserSession.expiration >= datetime.now(UTC)
        )

        result = await session.exec(statement)
        session_data = result.unique().one_or_none()
        return session_data.user if session_data else None

    @classmethod
    async def get_account_by_user_id(
        cls,
        user_id: int,
        provider: str,
        session: AsyncSession,
        purpose: str = "auth",
    ) -> UserAccount | None:
        """
        Get user account by user ID, provider, and purpose.

        Args:
            user_id: User's ID
            provider: Account provider (e.g., "google", "github", "credential")
            session: Async database session
            purpose: Account purpose ("auth" or "repo")

        Returns:
            UserAccount instance if found, None otherwise
        """
        statement = select(UserAccount).where(
            UserAccount.user_id == user_id,
            UserAccount.purpose == purpose,
            UserAccount.provider == provider,
        )
        result = await session.exec(statement)
        return result.one()
