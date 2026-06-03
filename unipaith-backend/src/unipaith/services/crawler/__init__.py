"""Spec 60 — the governed knowledge-engine service layer (§12).

Pipeline modules: ``sources`` (allowlist registry) · ``fetcher`` · ``extractor``
(SourceExtractionAgent) · ``normalizer`` · ``resolver`` · ``enrichment``
(write-path + authority) · ``change_detector`` · ``engine`` (orchestrator) ·
``seed`` (allowlist + reference seed) · ``reference_service`` (read API).
"""

from unipaith.services.crawler.engine import KnowledgeEngine
from unipaith.services.crawler.enrichment import EnrichmentWriter
from unipaith.services.crawler.reference_service import ReferenceService
from unipaith.services.crawler.sources import SOURCE_ALLOWLIST, SourceRegistry

__all__ = [
    "KnowledgeEngine",
    "EnrichmentWriter",
    "ReferenceService",
    "SourceRegistry",
    "SOURCE_ALLOWLIST",
]
