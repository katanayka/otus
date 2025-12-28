from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from hn_crawler.crawler import CrawlConfig, run_loop
from hn_crawler.storage import Storage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HN async crawler")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between crawls (0 for once)")
    parser.add_argument("--max-items", type=int, default=30, help="Max number of front-page items")
    parser.add_argument("--concurrency", type=int, default=8, help="Concurrent HTTP requests")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds")
    parser.add_argument("--db-path", type=Path, default=Path("data/hn_crawler.db"))
    parser.add_argument("--log", default=None, help="Log file path (default: stdout)")
    return parser.parse_args()


def configure_logging(log_path: str | None) -> None:
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )


async def main_async() -> None:
    args = parse_args()
    configure_logging(args.log)
    config = CrawlConfig(
        interval=args.interval,
        max_items=args.max_items,
        concurrency=args.concurrency,
        timeout=args.timeout,
        user_agent="otus-hn-crawler/1.0",
    )
    storage = Storage(args.db_path)

    def handler(items, links) -> None:
        storage.save_items(items)
        storage.save_links(links)
        logging.info("Stored %s items and %s links", len(items), sum(len(v) for v in links.values()))

    try:
        await run_loop(config, handler)
    finally:
        storage.close()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
