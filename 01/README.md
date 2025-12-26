# Log Analyzer

Nginx access log analyzer that builds an HTML report with per-URL stats.

## Features
- Finds the latest log by date in filename (`nginx-access-ui.log-YYYYMMDD[.gz]`).
- Parses URL and `request_time` from each line.
- Generates a report with count, time totals, averages, max, and median.
- Outputs JSON logs via `structlog`.
- Skips report generation if it already exists.

## Requirements
- Python 3.11+
- Poetry

## Install
Run these commands from the `01` directory.

```bash
poetry install
```

## Run
```bash
poetry run python log_analyzer.py
```

## Config
`--config` points to a JSON file (default: `config.json`). It is merged with
defaults from code; only overrides are needed.

Supported keys:
- `LOG_DIR`: directory with logs
- `REPORT_DIR`: output directory
- `REPORT_SIZE`: top N URLs by `time_sum`
- `PARSE_ERROR_PERC_MAX`: max allowed parsing error ratio (0-1)
- `REPORT_TEMPLATE`: HTML template path
- `TABLESORTER_PATH`: path to `jquery.tablesorter.min.js`
- `LOG_FILE`: optional log file path, `null` for stdout

Example `config.json`:
```json
{
  "LOG_DIR": ".",
  "REPORT_DIR": "./reports",
  "REPORT_SIZE": 1000,
  "PARSE_ERROR_PERC_MAX": 0.2,
  "LOG_FILE": null
}
```

Run with custom config:
```bash
poetry run python log_analyzer.py --config /path/to/config.json
```

## Reports
Reports are written to `REPORT_DIR` as `report-YYYY.MM.DD.html`. The script
also ensures `jquery.tablesorter.min.js` is present alongside the report.

## Development
```bash
poetry run ruff check .
poetry run black --check .
poetry run isort --check-only .
poetry run mypy src tests
poetry run pytest
poetry run pytest --cov=log_analyzer --cov-report=term-missing
```

## Docker
Build:
```bash
docker build -t log-analyzer .
```

Run (mount logs and output directory):
```bash
docker run --rm \
  -v /path/to/logs:/data/logs \
  -v /path/to/reports:/data/reports \
  -v /path/to/config.json:/data/config.json \
  log-analyzer --config /data/config.json
```

## CI
GitHub Actions runs ruff, black, isort, mypy, and pytest.
