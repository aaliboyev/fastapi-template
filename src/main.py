from fastapi import FastAPI
from fastapi.routing import APIRoute

from src.api.middlewares import SessionMiddleware
from src.api.router import router
from src.config import settings
from src.config.db.redis import redis_memory


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    store=redis_memory,
    http_only=True,
    secure=False,
    max_age=settings.SESSION_COOKIE_MAX_AGE,
    session_cookie=settings.SESSION_COOKIE_NAME,
    session_object="session",
)

app.include_router(router)
