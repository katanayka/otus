# Homework 12: Memcache Loader

Concurrent loader for tracker logs into multiple memcache instances.

## Structure
- `homework/memc_load.py` - loader script (multithreaded)
- `homework/appsinstalled.proto` - protobuf schema
- `homework/appsinstalled_pb2.py` - generated protobuf code
- `homework/README.md` - assignment text

## Requirements
- Python 3.10+
- memcached instances for idfa/gaid/adid/dvid (or run in `--dry` mode)
- protobuf 3.20.x (the bundled `appsinstalled_pb2.py` is generated with an older protoc)

## Setup
Run from the `12/` directory.

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m pip install -r dev_requirements.txt
```

## Run
```bash
python homework/memc_load.py --pattern="data/*.tsv.gz" --dry
```

Set a custom workers count:
```bash
python homework/memc_load.py --pattern="data/*.tsv.gz" --workers=8 --dry
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
GitHub Actions runs ruff and tests on every push/PR that touches `12/**`.
