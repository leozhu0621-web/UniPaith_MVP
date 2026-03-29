FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY alembic/ alembic/
COPY alembic.ini .
COPY src/ src/

USER appuser
EXPOSE 8000

CMD ["uvicorn", "unipaith.main:app", "--host", "0.0.0.0", "--port", "8000"]
