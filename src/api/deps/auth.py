from typing import Annotated, TypeAlias

from authx.exceptions import MissingTokenError
from fastapi import Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from src.api.deps.db import AsyncDBSession
from src.api.middlewares import SessionIntegration
from src.config import auth
from src.models.user import User
from src.services import UserService


async def check_token(request: Request):
    try:
        await auth.get_access_token_from_request(
            request, auth.config.JWT_TOKEN_LOCATION
        )
    except MissingTokenError:
        raise HTTPException(401, detail={"message": "Missing access token"})


async def get_session_user(request: Request, db_session: AsyncDBSession) -> User:
    """
    Get user from session, checking Redis cache first, then DB.

    Args:
        request: FastAPI request object
        db_session: Async database session

    Returns:
        User instance if authenticated

    Raises:
        HTTPException: 401 if user not authenticated
    """
    session: SessionIntegration = request.state.session

    # Try to get user from Redis session cache
    if user_dict := session.store.get("user"):
        return User.model_validate(user_dict)

    # If not in cache, try to load from database by session token
    user = await UserService.get_by_session_token(session.id, db_session)

    if user:
        # Cache user in session for future requests
        session["user"] = jsonable_encoder(user.model_dump())
        return user

    raise HTTPException(401, detail={"message": "Not authenticated"})


SessionUser: TypeAlias = Annotated[User, Depends(get_session_user)]
