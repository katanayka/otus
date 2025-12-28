from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from hn_crawler.models import Story


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                item_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                comments_url TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                UNIQUE(item_id, url),
                FOREIGN KEY(item_id) REFERENCES items(item_id)
            )
            """
        )
        self.conn.commit()

    def save_items(self, items: list[Story]) -> None:
        fetched_at = datetime.now(timezone.utc).isoformat()
        with self.conn:
            for item in items:
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO items (item_id, title, url, comments_url, fetched_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (item.item_id, item.title, item.url, item.comments_url, fetched_at),
                )

    def save_links(self, item_links: dict[int, list[str]]) -> None:
        with self.conn:
            for item_id, links in item_links.items():
                for url in links:
                    self.conn.execute(
                        """
                        INSERT OR IGNORE INTO links (item_id, url)
                        VALUES (?, ?)
                        """,
                        (item_id, url),
                    )

    def close(self) -> None:
        self.conn.close()
