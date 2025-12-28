from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from hn_crawler.models import Story

BASE_URL = "https://news.ycombinator.com/"


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    return urljoin(BASE_URL, url)


def parse_top(html: str) -> list[Story]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[Story] = []
    for row in soup.select("tr.athing"):
        item_id_raw = row.get("id")
        if not item_id_raw or not item_id_raw.isdigit():
            continue
        title_link = row.select_one("span.titleline a") or row.select_one("a.storylink")
        if title_link is None:
            continue
        title = title_link.get_text(strip=True)
        url = _normalize_url(title_link.get("href", ""))
        subtext = row.find_next_sibling("tr")
        comments_url = _normalize_url(f"item?id={item_id_raw}")
        if subtext is not None:
            comments_link = subtext.select_one("a[href^='item?id=']")
            if comments_link:
                comments_url = _normalize_url(comments_link.get("href", ""))
        items.append(
            Story(
                item_id=int(item_id_raw),
                title=title,
                url=url,
                comments_url=comments_url,
            )
        )
    return items


def parse_discussion_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    for link in soup.select("span.commtext a[href]"):
        href = link.get("href", "").strip()
        if not href:
            continue
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        if href.startswith("item?id=") or href.startswith("user?id="):
            continue
        links.add(_normalize_url(href))
    return sorted(links)


def limit_items(items: Iterable[Story], max_items: int | None) -> list[Story]:
    if not max_items or max_items <= 0:
        return list(items)
    return list(items)[:max_items]
