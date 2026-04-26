FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

COPY scripts/entrypoint.sh /usr/local/bin/ananse-web-entrypoint.sh
RUN chmod +x /usr/local/bin/ananse-web-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/ananse-web-entrypoint.sh"]
