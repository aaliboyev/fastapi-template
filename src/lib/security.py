import base64
import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from src.config import settings
from src.lib.generators import generate_token

ALGORITHM = "HS256"


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        to_encode = {"exp": expire, "sub": str(subject)}
    else:
        to_encode = {"sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Pre-hashes long passwords with SHA256 to work around bcrypt's 72-byte limit.
    """
    password_bytes = plain_password.encode("utf-8")

    # Pre-hash long passwords to work around bcrypt's 72-byte limit
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode("utf-8")

    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Pre-hashes long passwords with SHA256 to work around bcrypt's 72-byte limit.
    This ensures passwords longer than 72 bytes can still be hashed securely.
    """
    password_bytes = password.encode("utf-8")

    # Pre-hash long passwords to work around bcrypt's 72-byte limit
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode("utf-8")

    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode("utf-8")


def create_hmac(secret_key, message):
    message = message.encode("utf-8")
    secret_key = secret_key.encode("utf-8")
    hmac_digest = hmac.new(secret_key, message, digestmod=hashlib.sha256).digest()
    base64_encoded_hmac = base64.b64encode(hmac_digest).decode("utf-8")
    return base64_encoded_hmac


def create_signed_token(value: str, secret: str) -> str:
    signature = create_hmac(secret, value)
    signed_value = f"{value}.{signature}"
    return signed_value


def generate_and_sign_token(token_length: int, secret_key: str):
    return create_signed_token(generate_token(token_length), secret_key)


def verify_signed_token(token: str, secret: str):
    value, sig = token.split(".")
    return sig == create_hmac(secret, value)
