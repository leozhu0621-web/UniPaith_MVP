"""Spec 41 §2.1 / §5 — AdvisorMatcher.

Ranks faculty advisors by research-interest similarity to an applicant, both
directions (faculty see applicants who fit them; applicants see advisors who fit
them). MVP fidelity is a deterministic, calibrated overlap score over the
structured research-area / interest tags — the same shape as
``prospect_prioritizer`` and the YieldRiskScorer. The registry tier (``batch`` /
Haiku) documents the future embedding model (Spec 06 §4 vector infra): the
``research_alignment`` function below is the seam an embedding cosine would slot
into.

Pure and deterministic — it never 5xxes. The ranking itself is always available
(the service computes ``research_alignment`` regardless of the AI flag, so the
match surface works as a baseline); ``ai_graduate_v2_enabled`` only gates the
``rationale`` enrichment. Matching informs humans; faculty decide (§5 / 46 §6).
"""

from __future__ import annotations

import re

# Lightweight stopword set so common filler tokens don't inflate overlap. Kept
# intentionally small — research vocabulary is the signal, not English grammar.
_STOPWORDS = frozenset(
    {
        "and",
        "or",
        "the",
        "a",
        "an",
        "of",
        "for",
        "in",
        "on",
        "to",
        "with",
        "research",
        "study",
        "studies",
        "field",
        "area",
        "areas",
        "topic",
        "topics",
        "applied",
        "general",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(value: str) -> set[str]:
    """Normalized content tokens of a phrase (lowercased, stopwords dropped)."""
    return {t for t in _TOKEN_RE.findall(value.lower()) if t not in _STOPWORDS and len(t) > 1}


def _normalize_phrase(value: str) -> str:
    return " ".join(_TOKEN_RE.findall(value.lower()))


def _term_set(values: list[str] | None) -> tuple[set[str], set[str]]:
    """Return (token_set, normalized_phrase_set) for a list of interest strings."""
    tokens: set[str] = set()
    phrases: set[str] = set()
    for v in values or []:
        if not isinstance(v, str) or not v.strip():
            continue
        tokens |= _tokens(v)
        norm = _normalize_phrase(v)
        if norm:
            phrases.add(norm)
    return tokens, phrases


def research_alignment(
    applicant_interests: list[str] | None,
    advisor_areas: list[str] | None,
) -> tuple[float, list[str]]:
    """Deterministic research-interest similarity in ``[0, 100]``.

    Blends three signals so it ranks sensibly even on short tag lists:
    - ``coverage``  — share of the applicant's tokens the advisor also covers,
    - ``jaccard``   — symmetric token overlap (penalizes wildly different scope),
    - ``exact``     — exact normalized phrase matches (the strongest signal).

    Returns ``(score, shared_phrases)``. ``shared_phrases`` are the advisor areas
    that overlap the applicant's interests (used for the rationale + the UI).
    """
    a_tokens, a_phrases = _term_set(applicant_interests)
    b_tokens, b_phrases = _term_set(advisor_areas)
    if not a_tokens or not b_tokens:
        return 0.0, []

    inter = a_tokens & b_tokens
    union = a_tokens | b_tokens
    coverage = len(inter) / len(a_tokens)
    jaccard = len(inter) / len(union) if union else 0.0
    exact_phrases = a_phrases & b_phrases
    exact = len(exact_phrases) / max(1, len(a_phrases))

    score = 100.0 * (0.45 * coverage + 0.35 * jaccard + 0.20 * exact)
    score = max(0.0, min(100.0, round(score, 1)))

    # Shared phrases for display: advisor areas that share at least one token
    # with the applicant, exact matches first.
    shared: list[str] = []
    for area in advisor_areas or []:
        if not isinstance(area, str) or not area.strip():
            continue
        if _normalize_phrase(area) in exact_phrases:
            shared.insert(0, area.strip())
        elif _tokens(area) & inter:
            shared.append(area.strip())
    # De-dupe preserving order.
    seen: set[str] = set()
    shared = [s for s in shared if not (s.lower() in seen or seen.add(s.lower()))]
    return score, shared


def alignment_band(score: float) -> str:
    if score >= 60:
        return "strong"
    if score >= 30:
        return "moderate"
    return "weak"


class AdvisorMatcher:
    """Per-advisor research-fit score + plain-language rationale (deterministic)."""

    AGENT_NAME = "advisor_matcher"
    PROMPT_VERSION = "v1"

    def score(self, applicant_interests: list[str] | None, advisors: list[dict]) -> dict[str, dict]:
        """Return ``{faculty_id: {alignment_score, band, shared, rationale}}``.

        Each advisor dict must carry ``id`` and ``research_areas`` (list); ``name``
        is used in the rationale when present.
        """
        out: dict[str, dict] = {}
        for adv in advisors:
            fid = adv.get("id")
            if fid is None:
                continue
            score, shared = research_alignment(applicant_interests, adv.get("research_areas"))
            out[str(fid)] = {
                "alignment_score": score,
                "band": alignment_band(score),
                "shared": shared,
                "rationale": self.rationale(score, shared, adv.get("name")),
            }
        return out

    def rationale(self, score: float, shared: list[str], advisor_name: str | None = None) -> str:
        """A short, no-hype why for the score (the AI surface enrichment)."""
        band = alignment_band(score)
        who = advisor_name or "This advisor"
        if not shared:
            return (
                f"{who} has no overlapping research areas with the applicant's stated "
                "interests on file."
            )
        areas = ", ".join(shared[:4])
        lead = {
            "strong": "Strong research fit",
            "moderate": "Partial research fit",
            "weak": "Limited research fit",
        }[band]
        return f"{lead}: shared work in {areas}."


# ── Singleton ────────────────────────────────────────────────────────────────
_matcher: AdvisorMatcher | None = None


def get_advisor_matcher() -> AdvisorMatcher:
    global _matcher
    if _matcher is None:
        _matcher = AdvisorMatcher()
    return _matcher


def reset_advisor_matcher() -> None:
    global _matcher
    _matcher = None
