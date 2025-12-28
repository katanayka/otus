# Homework 13: HN Crawler

Asynchronous crawler for news.ycombinator.com that periodically stores the front-page items
and all links found in their discussion threads.

## Structure
- `hn_crawler/` - crawler package
- `tests/` - parser tests
- `data/hn_crawler.db` - SQLite storage (created on first run)

## Requirements
- Python 3.10+

## Setup
Run from the `13/` directory.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r dev_requirements.txt
```

## Run once
```bash
python -m hn_crawler --interval 0
```

## Run continuously
```bash
python -m hn_crawler --interval 60 --max-items 30 --concurrency 8
```

## CLI options
- `--interval` - seconds between runs (use `0` for one-shot)
- `--max-items` - number of front-page items to fetch
- `--concurrency` - parallel HTTP requests
- `--timeout` - request timeout (seconds)
- `--db-path` - SQLite path (default: `data/hn_crawler.db`)
- `--log` - log file path (default: stdout)

## Storage
Results are stored in `data/hn_crawler.db` with two tables:
- `items` (story metadata)
- `links` (discussion links per item)

To inspect the database with SQLite CLI:
```bash
sqlite3 data/hn_crawler.db
```

Then:
```sql
.tables
SELECT * FROM items LIMIT 5;
SELECT * FROM links LIMIT 5;
```

## Tests
```bash
pytest
```

## Lint
```bash
ruff check .
```

## Pre-commit
```bash
pre-commit install -c .pre-commit-config.yaml
pre-commit run --all-files
```

## CI
GitHub Actions runs ruff and tests on every push/PR that touches `13/**`.
