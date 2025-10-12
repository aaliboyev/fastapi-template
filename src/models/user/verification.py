from datetime import datetime, timedelta

from sqlmodel import Field

from src.models.base import BaseModelWithTimestamp


class UserVerification(BaseModelWithTimestamp, table=True):
    __tablename__ = "user_verifications"

    request_id: str
    value: str
    expiration: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(hours=1)
    )
