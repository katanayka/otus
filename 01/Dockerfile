FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY log_analyzer.py /app/
COPY report.html /app/
COPY jquery.tablesorter.min.js /app/
COPY config.json /app/config.json

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

ENTRYPOINT ["python", "log_analyzer.py"]
