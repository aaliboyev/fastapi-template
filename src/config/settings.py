import warnings
from typing import Annotated, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    Field,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.lib.utils import parse_cors


class ServerSettings(BaseSettings):
    """Server and API configuration settings."""

    PROJECT_NAME: str
    API_PREFIX: str = "/api"
    SERVER_HOST: str
    SERVER_PORT: int = 8000
    SERVER_PROTOCOL: str = "http"

    ENVIRONMENT: Literal["local", "remote", "dev", "staging", "production"] = "local"
    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = Field(
        default_factory=list
    )

    @property
    def base_url(self):
        return f"{self.SERVER_PROTOCOL}://{self.SERVER_HOST}:{self.SERVER_PORT}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.CORS_ORIGINS]


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""

    SECRET_KEY: str
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    SESSION_COOKIE_NAME: str = "sid"
    SESSION_COOKIE_MAX_AGE: int = 60 * 60 * 24 * 7
    # TODO: update type to EmailStr when sqlmodel supports it
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(
        self, var_name: str, value: str | None, environment: str = "production"
    ) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is still "changethis", '
                "for security, please change it for dev, staging and production deployments."
            )
            if environment in ["local", "remote"]:
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_url(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


class RedisSettings(BaseSettings):
    """Redis and Celery configuration settings."""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_base_url(self) -> str:
        """Build Redis URL from components if REDIS_URL is not set."""
        if self.REDIS_URL:
            return self.REDIS_URL

        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """Build Redis URL from components if REDIS_URL is not set."""
        if self.REDIS_URL:
            return self.REDIS_URL

        if self.REDIS_PASSWORD:
            return f"{self.redis_base_url}/{self.REDIS_DB}"
        else:
            return f"{self.redis_base_url}/{self.REDIS_DB}"


class EmailSettings(BaseSettings):
    """Email and SMTP configuration settings."""

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    # TODO: update type to EmailStr when sqlmodel supports it
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None
    # TODO: update type to EmailStr when sqlmodel supports it
    EMAIL_TEST_USER: str = "test@example.com"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)


class OAuthSettings(BaseSettings):
    """OAuth provider settings."""

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None


class Settings(
    ServerSettings,
    SecuritySettings,
    DatabaseSettings,
    RedisSettings,
    EmailSettings,
    OAuthSettings,
):
    """Main settings class that inherits from all setting groups."""

    model_config = SettingsConfigDict(
        env_file=".env",
        # secrets_dir="/run/secrets",
        env_ignore_empty=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY, self.ENVIRONMENT)
        self._check_default_secret(
            "POSTGRES_PASSWORD", self.POSTGRES_PASSWORD, self.ENVIRONMENT
        )
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD, self.ENVIRONMENT
        )
        return self


settings = Settings()  # type:  ignore

__all__ = ["settings"]
