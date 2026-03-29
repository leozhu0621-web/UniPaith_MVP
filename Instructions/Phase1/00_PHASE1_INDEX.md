# UniPaith MVP Backend — Phase 1: Foundation

**Goal:** Users can sign up, build profiles, institutions can publish programs. All core infrastructure in place.

## Task Order (feed to Cursor one at a time, in order)

| # | File | What it builds | Depends on |
|---|------|----------------|------------|
| 01 | `01_project_scaffolding.md` | Folder structure, pyproject.toml, Docker, env config | Nothing |
| 02 | `02_database_schema.md` | All PostgreSQL + pgvector tables, Alembic migrations | 01 |
| 03 | `03_authentication.md` | Cognito signup/login/token, auth middleware, role guards | 01, 02 |
| 04 | `04_student_endpoints.md` | Student profile CRUD, onboarding, preferences, academics, activities, test scores | 02, 03 |
| 05 | `05_institution_endpoints.md` | Institution + program CRUD, publishing flow | 02, 03 |
| 06 | `06_document_upload.md` | S3 presigned URLs, document records, file validation | 02, 03 |
| 07 | `07_seed_data.md` | Realistic seed data, Alembic seed script, dev bootstrap | 02-06 |

## Architecture Reference

- **Framework:** FastAPI (Python 3.12+)
- **Database:** PostgreSQL 16 + pgvector on Amazon RDS
- **Auth:** Amazon Cognito
- **File Storage:** Amazon S3
- **Deployment:** AWS ECS Fargate (containerized)
- **ORM:** SQLAlchemy 2.0 + Alembic migrations
- **Validation:** Pydantic v2

## How to Use These Specs

1. Open the spec file in Cursor
2. Select all text, use as context/prompt
3. Let Opus 4.6 generate the code
4. Review output, run tests, iterate
5. Move to next spec

Each spec is self-contained with full context so Cursor doesn't need prior conversation history.
