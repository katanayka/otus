# Тренажер по аннотации типов

Решения упражнений из https://python-type-challenges.zeabur.app.

## Структура
- `tasks/` — один файл = одно упражнение.
- Имена файлов соответствуют порядку/названию задач.

## Проверка типов (mypy)
Проверка не запускает код, она только анализирует аннотации.

Через Docker Compose:
```bash
docker compose run --rm typing
```

Через Docker напрямую:
```bash
docker build -t type-check-02 .
docker run --rm -v "${PWD}:/work" -w /work type-check-02 tasks
```

CI использует тот же `mypy`.
