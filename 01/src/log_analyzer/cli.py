from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional, Sequence

from log_analyzer.analyzer import analyze_log, load_config, setup_logging

DEFAULT_CONFIG: Dict[str, object] = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": ".",
    "REPORT_TEMPLATE": "./report.html",
    "TABLESORTER_PATH": "./jquery.tablesorter.min.js",
    "PARSE_ERROR_PERC_MAX": 0.2,
    "LOG_FILE": None,
}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nginx log analyzer")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to JSON config file",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logger = setup_logging(None)

    try:
        config = load_config(Path(args.config), DEFAULT_CONFIG)
    except (OSError, ValueError) as exc:
        logger.error("config_error", error=str(exc), config=str(args.config))
        return 1

    log_file = config.get("LOG_FILE")
    logger = setup_logging(str(log_file) if log_file else None)
    try:
        analyze_log(config, logger)
    except BaseException:
        logger.error("unexpected_error", exc_info=True)
        return 1
    return 0
