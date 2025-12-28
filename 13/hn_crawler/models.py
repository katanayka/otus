from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    item_id: int
    title: str
    url: str
    comments_url: str
