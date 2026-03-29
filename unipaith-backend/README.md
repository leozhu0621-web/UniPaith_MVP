# UniPaith Backend

AI-powered admissions platform backend API.

## Quick Start

```bash
# Start PostgreSQL + pgvector
docker-compose up -d

# Create virtualenv and install
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy env config
cp .env.example .env

# Run migrations
alembic upgrade head

# Start dev server
uvicorn unipaith.main:app --reload

# Run tests
pytest
```

## API Docs

With `DEBUG=true`, Swagger docs available at `http://localhost:8000/docs`.
