from __future__ import annotations

from pathlib import Path

import structlog

from log_analyzer.analyzer import (
    LOG_LINE_RE,
    LOG_NAME_RE,
    UrlStats,
    aggregate_stats,
    build_report_rows,
    find_latest_log,
    parse_log_lines,
)


def test_log_name_regex_matches_plain_and_gzip() -> None:
    assert LOG_NAME_RE.match("nginx-access-ui.log-20170630")
    assert LOG_NAME_RE.match("nginx-access-ui.log-20170630.gz")
    assert not LOG_NAME_RE.match("nginx-access-ui.log-20170630.bz2")


def test_log_line_regex() -> None:
    line = (
        "1.1.1.1 - 2.2.2.2 [30/Jun/2017:10:00:00 +0300] "
        '"GET /api/v1/test HTTP/1.1" 200 123 "-" "curl" "-" "-" "-" 0.123'
    )
    match = LOG_LINE_RE.search(line)
    assert match is not None
    assert match.group("url") == "/api/v1/test"
    assert match.group("request_time") == "0.123"


def test_parse_log_lines_handles_invalid_lines() -> None:
    lines = [
        "1.1.1.1 - - [30/Jun/2017:10:00:00 +0300]"
        + ' "GET /ok HTTP/1.1" 200 1 "-" "-" "-" "-" "-" 1.0',
        "broken line",
    ]
    parsed = list(parse_log_lines(lines))
    assert parsed[0] == ("/ok", 1.0)
    assert parsed[1] is None


def test_find_latest_log(tmp_path: Path) -> None:
    (tmp_path / "nginx-access-ui.log-20170629").write_text("test", encoding="utf-8")
    (tmp_path / "nginx-access-ui.log-20170630.gz").write_text("test", encoding="utf-8")
    (tmp_path / "nginx-access-ui.log-20170628.bz2").write_text("test", encoding="utf-8")

    latest = find_latest_log(tmp_path)
    assert latest is not None
    assert latest.path.name == "nginx-access-ui.log-20170630.gz"


def test_aggregate_stats_respects_error_threshold(tmp_path: Path) -> None:
    log_path = tmp_path / "nginx-access-ui.log-20170630"
    log_path.write_text("bad\nbad\n", encoding="utf-8")

    info = find_latest_log(tmp_path)
    assert info is not None
    logger = structlog.get_logger()
    aggregated = aggregate_stats(info, error_threshold=0.1, logger=logger)
    assert aggregated is None


def test_build_report_rows_sorting() -> None:
    stats = {
        "/a": UrlStats(count=2, time_sum=4.0, time_max=3.0, times=[1.0, 3.0]),
        "/b": UrlStats(count=1, time_sum=10.0, time_max=10.0, times=[10.0]),
    }
    rows = build_report_rows(stats, total_count=3, total_time=14.0, report_size=2)
    assert rows[0]["url"] == "/b"
    assert rows[1]["url"] == "/a"
