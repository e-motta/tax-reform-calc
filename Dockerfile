# syntax=docker/dockerfile:1

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app app \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY app/ app/
COPY rules/ rules/
COPY frontend/ frontend/

RUN uv sync --frozen --no-dev --no-editable \
    && chown -R app:app /app

USER app

ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
ENV FORWARDED_ALLOW_IPS="172.16.0.0/12,192.168.0.0/16,10.0.0.0/8"

EXPOSE 8000

CMD ["sh", "-c", "fastapi run app/main.py --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"$FORWARDED_ALLOW_IPS\""]
