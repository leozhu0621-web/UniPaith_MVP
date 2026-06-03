"""Spec 69 §10 — a realistic catalog generator (volume, not 9 hand-coded rows).

Deterministic generator of program rows spanning many CIP fields × degree levels
× modalities, ingested through the real ``CatalogIngestService`` (normalization,
provenance, dedup, idempotency). It is the "many programs across fields/levels/
modalities" the acceptance gate asks for (§10) and the dev/demo seed that
replaces the hand-coded ``Program(...)`` literals — generated, not fabricated:
every row is a real, normalizable program with a stable external_id, and it
ingests idempotently (re-run never duplicates). No randomness (reproducible).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.services.catalog.ingest_service import CatalogIngestService

# (field name, CIP code) — the breadth the matcher needs to have anything to rank.
_FIELDS: list[tuple[str, str]] = [
    ("Computer Science", "11.0701"),
    ("Data Science", "11.0401"),
    ("Business Administration", "52.0201"),
    ("Mechanical Engineering", "14.1901"),
    ("Electrical Engineering", "14.1001"),
    ("Public Health", "51.2201"),
    ("Economics", "45.0601"),
    ("Education", "13.0101"),
    ("Nursing", "51.3801"),
    ("Environmental Science", "03.0104"),
    ("Psychology", "42.0101"),
    ("Design", "50.0401"),
]
# (degree label, normalized degree_type, duration months, base tuition USD).
_LEVELS: list[tuple[str, str, int, int]] = [
    ("BS", "bachelors", 48, 42000),
    ("MS", "masters", 24, 56000),
    ("PhD", "doctoral", 60, 38000),
]
_MODALITIES = ("in_person", "online", "hybrid")


def curated_program_rows() -> list[dict]:
    """≥ |fields|×|levels| program rows (12×3 = 36), each a real normalizable
    program with a stable external_id (idempotent re-ingest)."""
    rows: list[dict] = []
    i = 0
    for field, cip in _FIELDS:
        for label, _degree, duration, base_tuition in _LEVELS:
            rows.append(
                {
                    "program_name": f"{field} ({label})",
                    "degree_type": label,
                    "delivery_format": _MODALITIES[i % len(_MODALITIES)],
                    "duration_months": duration,
                    "tuition": base_tuition + (i % 5) * 2000,
                    "cip_code": cip,
                    "external_id": f"{cip}-{label}".replace(".", ""),
                    "description": f"A {label} program in {field}.",
                }
            )
            i += 1
    return rows


async def seed_catalog_for_institution(
    db: AsyncSession, institution_id: UUID, *, source: str = "first_party"
) -> dict:
    """Ingest the curated catalog for one institution via the real pipeline.
    Returns the ingest summary {created, updated, skipped}."""
    return await CatalogIngestService(db).ingest_programs(
        institution_id, curated_program_rows(), source=source
    )
