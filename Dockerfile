# syntax=docker/dockerfile:1.4

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=ananseWifi.settings

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . /app

RUN chmod +x /app/scripts/entrypoint.sh \
    && DJANGO_USE_SQLITE=1 python manage.py collectstatic --noinput \
    && rm -f /app/db.sqlite3

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
