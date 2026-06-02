"""Spec 41 §2.2 / §5 — SoPInterestExtractor (extends `45` extraction).

Parses an applicant's statement of purpose into structured research-interest
tags and a short alignment summary. MVP fidelity is deterministic: it matches the
SoP text against the *department's actual research-area vocabulary* (the faculty
areas + the applicant's own stated interests) plus a small built-in research-domain
lexicon, so the tags are grounded in what the department actually works on rather
than free-association. The registry tier (``batch`` / Haiku) documents the future
LLM extractor (Spec 45) that this seam upgrades to.

Pure and deterministic — never 5xxes; the service only enriches when
``ai_graduate_v2_enabled`` is on, and otherwise leaves the applicant's stated
interests untouched (fall back to manual, §5).
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# A compact built-in research-domain lexicon. Only used to seed extraction when
# the department supplies no vocabulary of its own; the faculty areas are always
# the primary, higher-signal target.
_BUILTIN_DOMAINS = (
    "machine learning",
    "deep learning",
    "natural language processing",
    "computer vision",
    "reinforcement learning",
    "robotics",
    "artificial intelligence",
    "data science",
    "human computer interaction",
    "systems",
    "security",
    "cryptography",
    "networks",
    "databases",
    "theory",
    "algorithms",
    "bioinformatics",
    "computational biology",
    "genomics",
    "neuroscience",
    "public health",
    "epidemiology",
    "economics",
    "finance",
    "policy",
    "sociology",
    "philosophy",
    "history",
    "literature",
    "linguistics",
    "chemistry",
    "physics",
    "materials",
    "mechanical engineering",
    "electrical engineering",
    "civil engineering",
    "climate",
    "sustainability",
    "energy",
    "education",
)


def _tokens(value: str) -> list[str]:
    return _TOKEN_RE.findall(value.lower())


def _phrase_in_text(phrase: str, text_tokens: list[str], text_lower: str) -> bool:
    """True if ``phrase`` appears in the SoP — as a substring for multi-word
    phrases, or as a standalone token for single words."""
    p = phrase.lower().strip()
    if not p:
        return False
    if " " in p:
        return p in text_lower
    return p in text_tokens


def extract_interests(
    statement_of_purpose: str | None,
    vocabulary: list[str] | None = None,
    stated_interests: list[str] | None = None,
) -> list[str]:
    """Return de-duplicated research-interest tags found in the SoP.

    ``vocabulary`` is the department's research areas (highest signal); the
    applicant's ``stated_interests`` are folded in so an interest they wrote down
    *and* discuss in the SoP is reinforced. Falls back to the built-in lexicon
    when no vocabulary is supplied.
    """
    text = (statement_of_purpose or "").strip()
    if not text:
        # No SoP — the applicant's own stated interests are the best we have.
        return _dedupe(stated_interests or [])

    text_lower = text.lower()
    text_tokens = _tokens(text)

    candidates: list[str] = []
    candidates.extend(vocabulary or [])
    candidates.extend(stated_interests or [])
    if not (vocabulary or stated_interests):
        candidates.extend(_BUILTIN_DOMAINS)

    found = [
        c.strip()
        for c in candidates
        if isinstance(c, str) and c.strip() and _phrase_in_text(c, text_tokens, text_lower)
    ]
    # Always keep the applicant's stated interests even if not literally in the
    # SoP — they declared them, so they count.
    found.extend(s.strip() for s in (stated_interests or []) if isinstance(s, str) and s.strip())
    return _dedupe(found)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        key = v.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(v.strip())
    return out


class SoPInterestExtractor:
    """Statement-of-purpose → interest tags + alignment summary (deterministic)."""

    AGENT_NAME = "sop_interest_extractor"
    PROMPT_VERSION = "v1"

    def extract(
        self,
        statement_of_purpose: str | None,
        vocabulary: list[str] | None = None,
        stated_interests: list[str] | None = None,
    ) -> dict:
        tags = extract_interests(statement_of_purpose, vocabulary, stated_interests)
        return {
            "extracted_interests": tags,
            "alignment_summary": self._summary(tags, statement_of_purpose, vocabulary),
        }

    def _summary(self, tags: list[str], sop: str | None, vocabulary: list[str] | None) -> str:
        if not (sop or "").strip():
            if tags:
                return (
                    "No statement of purpose on file; using the applicant's stated "
                    f"interests: {', '.join(tags[:4])}."
                )
            return "No statement of purpose or stated research interests on file."
        if not tags:
            return (
                "The statement of purpose did not surface any research-area signals that "
                "match the department's work."
            )
        vocab_lower = {v.lower().strip() for v in (vocabulary or [])}
        aligned = [t for t in tags if t.lower().strip() in vocab_lower]
        lead = f"The statement of purpose emphasizes {', '.join(tags[:4])}."
        if aligned:
            return (
                f"{lead} Strong alignment with the department's work in {', '.join(aligned[:3])}."
            )
        return lead


# ── Singleton ────────────────────────────────────────────────────────────────
_extractor: SoPInterestExtractor | None = None


def get_sop_interest_extractor() -> SoPInterestExtractor:
    global _extractor
    if _extractor is None:
        _extractor = SoPInterestExtractor()
    return _extractor


def reset_sop_interest_extractor() -> None:
    global _extractor
    _extractor = None
