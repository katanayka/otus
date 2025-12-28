from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_path(value: str | None, default: Path) -> Path:
    if value is None:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


@dataclass(frozen=True)
class Settings:
    model_path: Path
    log_level: str
    auth_secret_key: str
    auth_algorithm: str
    access_token_expire_minutes: int
    admin_username: str
    admin_password: str
    user_username: str
    user_password: str


def get_settings() -> Settings:
    model_path = _resolve_path(
        os.getenv("MODEL_PATH"),
        BASE_DIR / "model" / "iris_rules.json",
    )
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    auth_secret_key = os.getenv("AUTH_SECRET_KEY", "change-me")
    auth_algorithm = os.getenv("AUTH_ALGORITHM", "HS256")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    user_username = os.getenv("USER_USERNAME", "user")
    user_password = os.getenv("USER_PASSWORD", "user")
    return Settings(
        model_path=model_path,
        log_level=log_level,
        auth_secret_key=auth_secret_key,
        auth_algorithm=auth_algorithm,
        access_token_expire_minutes=access_token_expire_minutes,
        admin_username=admin_username,
        admin_password=admin_password,
        user_username=user_username,
        user_password=user_password,
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
