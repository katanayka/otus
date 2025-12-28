from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings


@dataclass(frozen=True)
class User:
    username: str
    role: str


def authenticate_user(username: str, password: str, settings: Settings) -> User | None:
    if username == settings.admin_username and password == settings.admin_password:
        return User(username=username, role="admin")
    if username == settings.user_username and password == settings.user_password:
        return User(username=username, role="user")
    return None


def create_access_token(user: User, settings: Settings) -> str:
    expire_at = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": user.username,
        "role": user.role,
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)


def decode_access_token(token: str, settings: Settings) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return User(username=str(username), role=str(role))


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    settings = get_settings()
    return decode_access_token(credentials.credentials, settings)


def require_roles(*roles: str) -> Callable[[User], User]:
    allowed = set(roles)

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return user

    return _checker