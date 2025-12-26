# Clean Warehouse

DDD/Clean Architecture example for managing products and orders.

## Structure
- `homework_warehouse_management/domain` — domain models and services.
- `homework_warehouse_management/infrastructure` — SQLAlchemy ORM and repositories.
- `homework_warehouse_management/tests` — tests (pytest).

## Install dependencies
```bash
python -m pip install -r homework_warehouse_management/requirements.txt
python -m pip install -r homework_warehouse_management/dev_requirements.txt
```

## Run application
```bash
python homework_warehouse_management/main.py
```

## Run tests
```bash
pytest homework_warehouse_management/tests
```

With coverage:
```bash
pytest --cov=homework_warehouse_management/domain --cov-report=term-missing homework_warehouse_management/tests
```

## Lint
```bash
pylint homework_warehouse_management
```
