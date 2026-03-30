"""Phase 5 — Data Crawler pipeline.

Modules:
    source_registry  — CRUD + health tracking for DataSource entities
    engine           — HTTP fetcher / page downloader
    extractor        — LLM-based structured data extraction
    deduplicator     — Institution/program matching and classification
    ingestor         — Auto-ingest high-confidence records
    enrichment       — Supplementary data enrichment pipeline
    historical_seeder — Seed HistoricalOutcome from extracted stats
    review_queue     — Human review workflow for low-confidence records
    orchestrator     — Top-level pipeline coordinator
"""
