"""Spec 69 — program catalog ingestion (manual upload / editorial path)."""

from unipaith.services.catalog.ingest_service import (
    CATALOG_SOURCE_AUTHORITY,
    CatalogIngestService,
    catalog_authority,
    normalize_degree_type,
    normalize_modality,
)
from unipaith.services.catalog.sample_catalog import (
    curated_program_rows,
    seed_catalog_for_institution,
)

__all__ = [
    "CatalogIngestService",
    "CATALOG_SOURCE_AUTHORITY",
    "catalog_authority",
    "normalize_degree_type",
    "normalize_modality",
    "curated_program_rows",
    "seed_catalog_for_institution",
]
