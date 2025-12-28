# ML Model Serving API (Homework 08)

REST API for ML inference built with FastAPI. The service accepts a list of numeric
features and returns a model prediction for the Iris dataset. The model is a
simple rule-based classifier derived from Iris feature thresholds.

## Structure
- `app/` - FastAPI application and model code
- `model/iris_rules.json` - Iris rule-based model and metadata
- `tests/` - API tests

## Requirements
- Python 3.10+

## Install dependencies
```bash
python -m pip install -r requirements.txt
python -m pip install -r dev_requirements.txt
```

Run commands from the `08/` directory.

## Run locally
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Example request
Feature order: `sepal_length`, `sepal_width`, `petal_length`, `petal_width`.

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"features\":[5.1,3.5,1.4,0.2],\"request_id\":\"req-1\"}"
```

## Run tests
```bash
pytest
```

## Lint
```bash
ruff check .
```

## Docker
Build image:
```bash
docker build -t otus-ml-08 .
```

Run container:
```bash
docker run --rm -p 8000:8000 ^
  -e MODEL_PATH=/app/model/iris_rules.json ^
  -e LOG_LEVEL=INFO ^
  -e PORT=8000 ^
  otus-ml-08
```

Docker Compose:
```bash
docker compose up --build
```

## Environment variables
- `MODEL_PATH` - path to model file (default: `model/iris_rules.json`)
- `LOG_LEVEL` - log level (default: `INFO`)
- `PORT` - port for uvicorn (default: `8000`)
