"""Shared deterministic extraction + normalization helpers.

The Spec 60 crawler / info-gathering automation (source registry, fetcher,
orchestrator, seeders, enrichment write-path, change detector) was removed.
What remains are the network-free, deterministic helpers still used elsewhere:

- ``extractor`` — ``SourceExtractionAgent`` (grounded field extraction), consumed
  by the ML eval harness (``ai/evals/extraction_adapter``).
- ``schemas`` — ``DomainSchema`` / ``schema_for`` (the extraction field schemas).
- ``normalizer`` — ``normalize_cip`` etc., used by catalog ingestion.

Consumers import these submodules directly; nothing is re-exported here.
"""
