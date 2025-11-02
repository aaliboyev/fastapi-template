from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from src.api.deps.auth import SessionUser
from src.api.deps.db import AsyncDBSession
from src.api.middlewares import SessionIntegration
from src.config import settings
from src.models.user import User
from src.models.user.session import UserSession
from src.schema.user import UserLogin, UserPublic, UserRegister
from src.services import UserService

router = APIRouter()


@router.post("/register", response_model=UserPublic)
async def register(user_in: UserRegister, db_session: AsyncDBSession) -> User:
    """
    Register a new user.

    Creates a new user account, establishes a session, and caches user data in Redis.
    """
    # Check if user already exists
    existing_user = await UserService.get_by_email(user_in.email, db_session)
    if existing_user:
        raise HTTPException(400, detail={"message": "Email already registered"})

    user = await UserService.register(user_in, db_session)

    return user


@router.post("/login", response_model=UserPublic)
async def login(
    request: Request,
    response: Response,
    credentials: UserLogin,
    db_session: AsyncDBSession,
) -> User:
    """
    Login user with email and password.

    Authenticates the user, creates a session, and caches user data in Redis.
    """
    session: SessionIntegration = request.state.session

    # Authenticate user
    user = await UserService.authenticate(
        credentials.email, credentials.password, db_session
    )

    if not user:
        response.set_cookie("auth", "false")
        raise HTTPException(401, detail={"message": "Invalid email or password"})

    # Create user session in database
    user_session = UserSession(
        user_id=user.id,
        token=session.id,
        expiration=datetime.now(UTC)
        + timedelta(seconds=settings.SESSION_COOKIE_MAX_AGE),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db_session.add(user_session)
    await db_session.commit()

    # Cache user in Redis session
    session["user"] = jsonable_encoder(user.model_dump())
    response.set_cookie("auth", "true")
    return user


@router.get("/me", response_model=UserPublic)
async def get_current_user(user: SessionUser) -> User:
    """
    Get current authenticated user.

    Returns the currently logged-in user based on session.
    """
    return user


@router.post("/logout")
async def logout(
    _: SessionUser, response: Response, request: Request, db_session: AsyncDBSession
) -> dict:
    """
    Logout current user.

    Clears the session from both Redis and database.
    """
    session: SessionIntegration = request.state.session
    await UserService.logout(session.id, db_session)
    await session.clear()
    response.set_cookie("auth", "false")
    return {"message": "Logged out successfully"}
