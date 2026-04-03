FROM python:3.12-slim AS builder

# implicit (ALS) builds C extensions; slim image has no compiler by default
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY alembic/ alembic/
COPY alembic.ini .
COPY src/ src/
COPY scripts/ scripts/
COPY docker-entrypoint.sh .

RUN chmod +x docker-entrypoint.sh

USER appuser
EXPOSE 8000

ENV PYTHONPATH=/app/src

ENTRYPOINT ["./docker-entrypoint.sh"]
# Single worker: one APScheduler + consistent in-memory engine state; multi-worker duplicated ticks.
CMD ["uvicorn", "unipaith.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
