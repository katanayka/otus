import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

from log_analyzer.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
