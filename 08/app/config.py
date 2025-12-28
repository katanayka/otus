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


def get_settings() -> Settings:
    model_path = _resolve_path(
        os.getenv("MODEL_PATH"),
        BASE_DIR / "model" / "iris_rules.json",
    )
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    return Settings(model_path=model_path, log_level=log_level)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
