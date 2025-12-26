# Scoring API Tests

Unit tests and store implementation for the scoring API.

## Structure
- `homework/api.py` — HTTP API and request validation.
- `homework/scoring.py` — scoring and interests logic.
- `homework/store.py` — key-value store wrapper with retries.
- `homework/test.py` — unit tests.

By default the server uses `InMemoryClient`. To plug a real store, update
`client_factory` in `homework/api.py`.

## Run tests
```bash
python homework/test.py
```

## Lint (pep8)
```bash
python -m pip install ruff
ruff check homework
```
