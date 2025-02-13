from datetime import datetime, timedelta

import jwt
from fastapi.security import HTTPBearer
from pytz import timezone

from core.configs import settings

oauth2_schema = HTTPBearer(bearerFormat="JWT", auto_error=False)


def create_token(
    token_type: str,
    lifetime: timedelta,
    sub: str,
    data_type: str,
    is_active: bool,
):
    payload = {}
    timezone_ba = timezone("America/Bahia")
    expires_in = datetime.now(tz=timezone_ba) + lifetime

    payload["type"] = token_type
    payload["exp"] = expires_in
    payload["iat"] = datetime.now(tz=timezone_ba)
    payload["sub"] = str(sub)
    payload["scopes"] = data_type
    payload["is_active"] = is_active

    return jwt.encode(payload, settings.JWT_KEY, algorithm=settings.ALGORITHM)


def create_access_token(sub: str, data_type: str, is_active: bool):
    return create_token(
        token_type="access_token",
        lifetime=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        sub=sub,
        data_type=data_type,
        is_active=is_active,
    )