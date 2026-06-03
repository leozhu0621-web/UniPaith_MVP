"""Spec 62 §2/§8 — the versioned golden-set case store.

The golden set is the quality source of truth and **grows from real failures**
(§2). It lives as fixtures in-repo (``fixtures/<consumer>/``); a run persists
per-case-per-run scores to ``eval_results`` and upserts the cases to
``eval_cases`` (the DB write-path lives in ``eval_harness_service`` so this module
stays pure / DB-free and importable by the transparency layer).

One loader per consumer turns its on-disk fixtures into the shared
:class:`~unipaith.ai.evals.adapter.EvalCase`. The chatbot golden set reuses the
per-dimension constitution cases the chatbot adapter already materializes into
(one source of truth on disk); the extraction golden set is the labeled pages in
``fixtures/extraction/``.
"""

from __future__ import annotations

import json
from pathlib import Path

from unipaith.ai.evals.adapter import EvalCase

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Golden-set version per consumer. Bumped when the rubric or case set changes in
# a way that invalidates prior runs (§6 — a regression is measured within a
# version).
GOLDEN_VERSIONS: dict[str, str] = {"chatbot": "v1", "extraction": "v1"}


def _load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("//"):
                out.append(json.loads(line))
    return out


def load_extraction_cases() -> list[EvalCase]:
    rows = _load_jsonl(FIXTURES_DIR / "extraction" / "extraction_cases.jsonl")
    version = GOLDEN_VERSIONS["extraction"]
    return [
        EvalCase(
            id=r["id"],
            consumer="extraction",
            domain=r.get("domain"),
            payload=r.get("payload", {}),
            expected=r.get("expected", {}),
            dimension=r.get("dimension"),
            severity=r.get("severity", "normal"),
            source=r.get("source", "curated"),
            version=version,
        )
        for r in rows
    ]


def load_chatbot_cases() -> list[EvalCase]:
    """The chatbot golden set = the per-dimension constitution cases (the curated
    set the chatbot adapter's ``materialize`` feeds and the judge grades). Loaded
    through the runner's own loader so there is one source of truth on disk."""
    from unipaith.ai.evals.runner import load_constitution_cases

    version = GOLDEN_VERSIONS["chatbot"]
    out: list[EvalCase] = []
    for r in load_constitution_cases():
        out.append(
            EvalCase(
                id=r.get("id", ""),
                consumer="chatbot",
                agent="student",
                prompt=r.get("prompt", ""),
                dimension=r.get("dimension"),
                must_not_contain=tuple(r.get("must_not_contain", []) or []),
                source=r.get("source", "curated"),
                version=version,
            )
        )
    return out


_LOADERS = {
    "chatbot": load_chatbot_cases,
    "extraction": load_extraction_cases,
}


def consumers() -> list[str]:
    return list(_LOADERS)


def load_cases(consumer: str) -> list[EvalCase]:
    loader = _LOADERS.get(consumer)
    return loader() if loader else []


def golden_count(consumer: str) -> int:
    return len(load_cases(consumer))


def version(consumer: str) -> str:
    return GOLDEN_VERSIONS.get(consumer, "v1")
