from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

from hn_crawler.models import Story
from hn_crawler.parser import BASE_URL, limit_items, parse_discussion_links, parse_top


@dataclass(frozen=True)
class CrawlConfig:
    interval: int
    max_items: int
    concurrency: int
    timeout: int
    user_agent: str


async def fetch_text(
    session: aiohttp.ClientSession,
    url: str,
    semaphore: asyncio.Semaphore,
    retries: int = 2,
) -> str:
    for attempt in range(retries + 1):
        try:
            async with semaphore:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception as exc:
            if attempt >= retries:
                raise
            logging.debug("Retry %s for %s due to %s", attempt + 1, url, exc)
            await asyncio.sleep(1)
    return ""


async def fetch_discussion_links(
    session: aiohttp.ClientSession,
    story: Story,
    semaphore: asyncio.Semaphore,
) -> tuple[int, list[str]]:
    try:
        html = await fetch_text(session, story.comments_url, semaphore)
        links = parse_discussion_links(html)
        return story.item_id, links
    except Exception as exc:
        logging.warning("Failed to fetch discussion for %s: %s", story.item_id, exc)
        return story.item_id, []


async def crawl_once(config: CrawlConfig) -> tuple[list[Story], dict[int, list[str]]]:
    timeout = aiohttp.ClientTimeout(total=config.timeout)
    headers = {"User-Agent": config.user_agent}
    semaphore = asyncio.Semaphore(config.concurrency)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        top_html = await fetch_text(session, BASE_URL, semaphore)
        items = limit_items(parse_top(top_html), config.max_items)
        tasks = [fetch_discussion_links(session, item, semaphore) for item in items]
        results = await asyncio.gather(*tasks)
    item_links = {item_id: links for item_id, links in results}
    return items, item_links


async def run_loop(config: CrawlConfig, handler: Any) -> None:
    while True:
        items, links = await crawl_once(config)
        handler(items, links)
        if config.interval <= 0:
            break
        await asyncio.sleep(config.interval)
