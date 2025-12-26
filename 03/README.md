# Scoring API

Реализация декларативного описания полей и валидации запросов к HTTP API.

## Структура
- `homework/api.py` — основная логика API и валидации.
- `homework/scoring.py` — функции подсчета скора и интересов.
- `homework/test.py` — набор тестов.

## Запуск сервера
```bash
python homework/api.py --port 8080
```

Пример запроса:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "TOKEN", "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru"}}' \
  http://127.0.0.1:8080/method/
```

## Запуск тестов
```bash
python homework/test.py
```

## Проверка pep8
```bash
python -m pip install ruff
ruff check homework
```
