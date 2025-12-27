## Structure
- `config/` - project settings and URLs
- `polls/` - tutorial app

## Requirements
- Python 3.10-3.12

## Install dependencies
```bash
python -m pip install -r 07/requirements.txt
python -m pip install -r 07/dev_requirements.txt
```

## Database and migrations
```bash
python manage.py migrate
```

## Run development server
```bash
python manage.py runserver
```

## Run tests
```bash
python manage.py test
```

## Lint
```bash
ruff check .
```

## Production settings (12-factor)
Configure the app using environment variables:

- `DJANGO_ENV` - `production` or `development`
- `DJANGO_DEBUG` - `true`/`false`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS` - comma-separated
- `DATABASE_URL` - e.g. `postgres://user:pass@host:5432/dbname`

Example:
```bash
set DJANGO_ENV=production
set DJANGO_SECRET_KEY=change-me
set DJANGO_ALLOWED_HOSTS=example.com
set DATABASE_URL=sqlite:///db.sqlite3
```

Collect static files and run with gunicorn:
```bash
python manage.py collectstatic

# From 07/
gunicorn config.wsgi:application
```

## Docker
Build image:
```bash
docker build -t otus-django-07 07
```

Run container:
```bash
docker run --rm -p 8000:8000 ^
  -e DJANGO_ENV=production ^
  -e DJANGO_DEBUG=false ^
  -e DJANGO_SECRET_KEY=change-me ^
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 ^
  -e DJANGO_SECURE_SSL_REDIRECT=false ^
  -e DATABASE_URL=sqlite:////app/data/db.sqlite3 ^
  -e PORT=8000 ^
  -v %cd%/07/data:/app/data ^
  otus-django-07
```

Docker Compose:
```bash
docker compose -f docker-compose.yml up --build
```

## Notes
- For local development, SQLite is used by default.
- If `DJANGO_ENV=production` and `DATABASE_URL` or `DJANGO_SECRET_KEY` are missing,
  the app will refuse to start.
