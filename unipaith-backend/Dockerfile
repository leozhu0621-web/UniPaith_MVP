# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

# implicit (ALS) builds C extensions; slim image has no compiler by default
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install third-party dependencies first, keyed only on pyproject.toml. This is
# the slow layer (compiling asyncpg/scipy/xgboost/shap/hdbscan/lxml wheels) and
# is reused whenever dependencies are unchanged — even when app source changes.
# The pip cache mount also persists built wheels across CI builds.
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); open('/tmp/reqs.txt','w').write(chr(10).join(d['project']['dependencies']))" \
    && pip install -r /tmp/reqs.txt

# Then install just the local package (fast; deps already satisfied).
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-deps .

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY alembic/ alembic/
COPY alembic.ini .
COPY src/ src/
COPY scripts/ scripts/
COPY data/ data/
COPY docker-entrypoint.sh .

RUN chmod +x docker-entrypoint.sh

USER appuser
EXPOSE 8000

ENV PYTHONPATH=/app/src

ENTRYPOINT ["./docker-entrypoint.sh"]
# Single worker: one APScheduler + consistent in-memory engine state; multi-worker duplicated ticks.
CMD ["uvicorn", "unipaith.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
