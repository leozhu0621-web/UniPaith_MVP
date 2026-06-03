"""Spec 69 — program catalog ingestion (the pipeline that makes the catalog real)."""

from unipaith.services.catalog.ingest_service import (
    CATALOG_SOURCE_AUTHORITY,
    CatalogIngestService,
    catalog_authority,
    normalize_degree_type,
    normalize_modality,
)

__all__ = [
    "CatalogIngestService",
    "CATALOG_SOURCE_AUTHORITY",
    "catalog_authority",
    "normalize_degree_type",
    "normalize_modality",
]
