from __future__ import annotations

import gzip
import json
import logging
import re
import shutil
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, TypedDict, cast

import structlog
from structlog.stdlib import BoundLogger

LOG_NAME_RE = re.compile(r"nginx-access-ui\.log-(\d{8})(?:\.gz)?$")
LOG_LINE_RE = re.compile(
    r'"\S+ (?P<url>\S+) \S+" .*? (?P<request_time>\d+(?:\.\d+)?)\s*$'
)


@dataclass(frozen=True)
class LogFileInfo:
    path: Path
    date: datetime
    is_gzip: bool


def setup_logging(log_path: Optional[str]) -> BoundLogger:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    handler: logging.Handler
    if log_path:
        handler = logging.FileHandler(log_path)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return cast(BoundLogger, structlog.get_logger())


@dataclass
class UrlStats:
    count: int
    time_sum: float
    time_max: float
    times: List[float]


class ReportRow(TypedDict):
    url: str
    count: int
    count_perc: float
    time_sum: float
    time_perc: float
    time_avg: float
    time_max: float
    time_med: float


def get_int_value(config: Dict[str, object], key: str) -> int:
    value = config[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Config '{key}' must be an int")
    return value


def get_float_value(config: Dict[str, object], key: str) -> float:
    value = config[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Config '{key}' must be a float")
    return float(value)


def get_str_value(config: Dict[str, object], key: str) -> str:
    value = config[key]
    if not isinstance(value, str):
        raise ValueError(f"Config '{key}' must be a string")
    return value


def load_config(
    config_path: Path, default_config: Dict[str, object]
) -> Dict[str, object]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    try:
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Config parse error: {config_path}") from exc

    if not isinstance(loaded, dict):
        raise ValueError("Config must be a JSON object")

    merged = dict(default_config)
    merged.update(loaded)
    return merged


def find_latest_log(log_dir: Path) -> Optional[LogFileInfo]:
    latest: Optional[LogFileInfo] = None
    if not log_dir.exists() or not log_dir.is_dir():
        return None

    for entry in log_dir.iterdir():
        if not entry.is_file():
            continue
        match = LOG_NAME_RE.match(entry.name)
        if not match:
            continue
        log_date = datetime.strptime(match.group(1), "%Y%m%d")
        is_gzip = entry.name.endswith(".gz")
        if latest is None or log_date > latest.date:
            latest = LogFileInfo(path=entry, date=log_date, is_gzip=is_gzip)
    return latest


def parse_log_lines(lines: Iterable[str]) -> Iterator[Optional[Tuple[str, float]]]:
    for line in lines:
        match = LOG_LINE_RE.search(line)
        if not match:
            yield None
            continue
        url = match.group("url")
        try:
            request_time = float(match.group("request_time"))
        except ValueError:
            yield None
            continue
        yield url, request_time


def aggregate_stats(
    log_info: LogFileInfo,
    error_threshold: float,
    logger: BoundLogger,
) -> Optional[Tuple[Dict[str, UrlStats], int, float]]:
    opener = gzip.open if log_info.is_gzip else open
    total = 0
    errors = 0
    total_time = 0.0
    stats: Dict[str, UrlStats] = {}

    with opener(log_info.path, "rt", encoding="utf-8", errors="replace") as file_obj:
        for parsed in parse_log_lines(file_obj):
            total += 1
            if parsed is None:
                errors += 1
                continue
            url, request_time = parsed
            total_time += request_time
            bucket = stats.setdefault(
                url, UrlStats(count=0, time_sum=0.0, time_max=0.0, times=[])
            )
            bucket.count += 1
            bucket.time_sum += request_time
            bucket.time_max = max(bucket.time_max, request_time)
            bucket.times.append(request_time)

    if total == 0:
        logger.info("empty_log", path=str(log_info.path))
        return None

    error_ratio = errors / total
    if error_ratio > error_threshold:
        logger.error(
            "too_many_parse_errors",
            path=str(log_info.path),
            error_ratio=error_ratio,
            error_threshold=error_threshold,
            total=total,
            errors=errors,
        )
        return None

    return stats, total, total_time


def build_report_rows(
    stats: Dict[str, UrlStats],
    total_count: int,
    total_time: float,
    report_size: int,
) -> List[ReportRow]:
    rows: List[ReportRow] = []
    for url, data in stats.items():
        time_avg = data.time_sum / data.count if data.count else 0.0
        time_med = statistics.median(data.times) if data.times else 0.0
        count_perc = (data.count * 100 / total_count) if total_count else 0.0
        time_perc = (data.time_sum * 100 / total_time) if total_time else 0.0
        rows.append(
            ReportRow(
                url=url,
                count=data.count,
                count_perc=count_perc,
                time_sum=data.time_sum,
                time_perc=time_perc,
                time_avg=time_avg,
                time_max=data.time_max,
                time_med=time_med,
            )
        )

    rows.sort(key=lambda item: item["time_sum"], reverse=True)
    return rows[:report_size]


def ensure_tablesorter(
    report_dir: Path, source_path: Path, logger: BoundLogger
) -> None:
    target_path = report_dir / source_path.name
    if target_path.exists():
        return
    if not source_path.exists():
        logger.error("tablesorter_missing", source=str(source_path))
        return
    shutil.copyfile(source_path, target_path)


def render_report(
    template_path: Path, report_path: Path, rows: List[ReportRow]
) -> None:
    table_json = json.dumps(rows)
    template = Template(template_path.read_text(encoding="utf-8"))
    report_body = template.safe_substitute(table_json=table_json)
    report_path.write_text(report_body, encoding="utf-8")


def analyze_log(
    config: Dict[str, object],
    logger: BoundLogger,
) -> Optional[Path]:
    log_dir = Path(get_str_value(config, "LOG_DIR"))
    report_dir = Path(get_str_value(config, "REPORT_DIR"))
    report_size = get_int_value(config, "REPORT_SIZE")
    error_threshold = get_float_value(config, "PARSE_ERROR_PERC_MAX")
    template_path = Path(get_str_value(config, "REPORT_TEMPLATE"))
    tablesorter_path = Path(get_str_value(config, "TABLESORTER_PATH"))

    log_info = find_latest_log(log_dir)
    if log_info is None:
        logger.info("no_logs", log_dir=str(log_dir))
        return None

    report_dir.mkdir(parents=True, exist_ok=True)
    report_name = f"report-{log_info.date.strftime('%Y.%m.%d')}.html"
    report_path = report_dir / report_name
    if report_path.exists():
        logger.info("report_exists", report=str(report_path))
        return report_path

    aggregated = aggregate_stats(log_info, error_threshold, logger)
    if aggregated is None:
        return None
    stats, total_count, total_time = aggregated

    rows = build_report_rows(stats, total_count, total_time, report_size)
    render_report(template_path, report_path, rows)
    ensure_tablesorter(report_dir, tablesorter_path, logger)
    logger.info("report_ready", report=str(report_path))
    return report_path
