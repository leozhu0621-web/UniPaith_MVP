"""Spec 42 §4.17 — PromptCoach (behavioral-prompt inference layer).

Deterministic engine that turns a student's behavioral-prompt responses + story
bank into the §4.17 outputs: STAR completeness, competency-coverage map/gaps,
interview readiness band+score, story↔prompt matching, revision priorities,
authenticity-risk flags, word-count compliance, and a personalized practice
plan.

Pure and deterministic — it never 5xxes (same stance as ``prospect_prioritizer``
/ ``yield_risk_scorer``). ``PromptLibraryService`` applies this overlay only when
``ai_prompt_library_v2_enabled`` is on; the raw catalog + responses are always
served regardless. The registry tier (``workhorse`` / Sonnet) documents the
future LLM swap-in (richer question generation + practice-plan narration), which
would fall back to this engine on any failure.
"""

from __future__ import annotations

import re

# ── STAR cue lexicon ─────────────────────────────────────────────────────────
# Lower-cased substring cues per STAR element. Heuristic, intentionally generous
# on the "present" side — the UI uses these to nudge, not to grade.
_STAR_CUES: dict[str, tuple[str, ...]] = {
    "situation": (
        "when ",
        "during ",
        "at the time",
        "we were",
        "there was",
        "the situation",
        "faced with",
        "in my role",
        "in my position",
        "our team was",
        "initially",
        "back when",
        "as a ",
        "while ",
    ),
    "task": (
        "needed to",
        "my goal",
        "my task",
        "my job was",
        "responsible for",
        "had to",
        "the challenge was",
        "the problem was",
        "the goal was",
        "was tasked",
        "my objective",
        "required to",
        "expected to",
        "asked me to",
        "set out to",
    ),
    "action": (
        "so i ",
        "i led",
        "i built",
        "i created",
        "i organized",
        "i decided",
        "i implemented",
        "i proposed",
        "i reached out",
        "i started",
        "i designed",
        "i coordinated",
        "i developed",
        "i launched",
        "i resolved",
        "i negotiated",
        "i wrote",
        "i analyzed",
        "i set up",
        "i took",
        "my approach",
        "to address",
        "i worked",
        "i began",
        "i spent",
    ),
    "result": (
        "as a result",
        "resulted in",
        "achieved",
        "increased",
        "decreased",
        "reduced",
        "improved",
        "grew",
        "we won",
        "ultimately",
        "in the end",
        "the outcome",
        "led to",
        "raised",
        "saved",
        "delivered",
        "completed",
        "succeeded",
        "ended up",
        "by the end",
    ),
    "reflection": (
        "i learned",
        "in retrospect",
        "looking back",
        "this taught me",
        "i realized",
        "next time",
        "takeaway",
        "going forward",
        "i grew",
        "reflecting",
        "this experience",
        "i understood",
        "made me realize",
        "i now ",
        "since then",
    ),
}

# A first-person past-tense verb is strong evidence of an "action" beat even when
# no canonical cue matches (e.g. "I rebuilt the intake form overnight").
_FIRST_PERSON_ACTION = re.compile(r"\bi\s+[a-z]+ed\b", re.IGNORECASE)

# The canonical interview set readiness is scored against (matches the seed
# catalog in services/prompt_library_seed.py). Keeps readiness interpretable
# even though the full catalog has ~70 prompts.
CORE_INTERVIEW_KEYS: tuple[str, ...] = (
    "tell_me_about_yourself_2min",
    "proudest_accomplishment",
    "biggest_failure",
    "conflict_with_teammate",
    "leadership_without_title",
    "why_this_field",
    "why_now",
    "future_vision",
)


# ── Per-response analysis ────────────────────────────────────────────────────
def detect_star(text: str | None) -> dict[str, bool]:
    """STAR-completeness flags from response text (system-derived, §3.19)."""
    out = {k: False for k in ("situation", "task", "action", "result", "reflection")}
    if not text:
        return out
    low = text.lower()
    for element, cues in _STAR_CUES.items():
        if any(cue in low for cue in cues):
            out[element] = True
    if not out["action"] and _FIRST_PERSON_ACTION.search(text):
        out["action"] = True
    return out


_PCT = re.compile(r"\d+(?:\.\d+)?\s*%")
_MONEY = re.compile(r"[$€£]\s*\d|\b\d+\s*(?:dollars|usd|eur|gbp|k\b)", re.IGNORECASE)
_TIME = re.compile(
    r"\b\d+\s*(?:hours?|hrs?|days?|weeks?|months?|years?|minutes?|mins?)\b", re.IGNORECASE
)
_COUNT = re.compile(
    r"\b\d+\s*(?:people|students|members|users|participants|attendees|volunteers|customers|"
    r"clients|teams?|projects?|events?)\b",
    re.IGNORECASE,
)
_ANY_NUM = re.compile(r"\b\d{2,}\b")


def detect_impact(text: str | None) -> tuple[bool, str | None, str | None]:
    """Return (present, type, value_band). type ∈ §3.19 impact_metric_type."""
    if not text:
        return (False, None, None)
    if _PCT.search(text):
        m = _PCT.search(text)
        val = float(re.sub(r"[^\d.]", "", m.group(0)))
        band = "large" if val >= 50 else "medium" if val >= 10 else "small"
        return (True, "percent", band)
    if _MONEY.search(text):
        return (True, "dollar", _num_band(text))
    if _TIME.search(text):
        return (True, "time", _num_band(text))
    if _COUNT.search(text):
        return (True, "count", _num_band(text))
    if _ANY_NUM.search(text):
        return (True, "scale", _num_band(text))
    return (False, None, None)


def _num_band(text: str) -> str:
    nums = [int(n) for n in re.findall(r"\b\d{1,9}\b", text)]
    if not nums:
        return "small"
    top = max(nums)
    return "large" if top >= 100 else "medium" if top >= 10 else "small"


def word_count(text: str | None) -> int:
    return len(text.split()) if text else 0


def word_count_compliance(text: str | None, word_limit: int | None) -> str:
    """under | met | over | none (no limit)."""
    if not word_limit:
        return "none"
    wc = word_count(text)
    if wc == 0:
        return "under"
    # ±15% tolerance band counts as "met".
    if wc < word_limit * 0.85:
        return "under"
    if wc > word_limit * 1.15:
        return "over"
    return "met"


def authenticity_risk_flags(text: str | None) -> list[str]:
    """Light heuristic — generic / over-optimized / AI-pattern (§4.17)."""
    if not text:
        return []
    flags: list[str] = []
    low = text.lower()
    wc = word_count(text)
    if wc and wc < 25:
        flags.append("generic")
    buzz = (
        "synergy",
        "leverage",
        "passionate",
        "hardworking",
        "team player",
        "go-getter",
        "results-driven",
        "detail-oriented",
        "think outside the box",
    )
    if sum(b in low for b in buzz) >= 3:
        flags.append("over_optimized")
    ai_tells = (
        "as an ai",
        "in today's fast-paced world",
        "it is important to note",
        "furthermore, ",
        "moreover, ",
        "in conclusion,",
    )
    if sum(t in low for t in ai_tells) >= 2:
        flags.append("AI_pattern")
    return flags


def analyze_response(text: str | None, word_limit: int | None = None) -> dict:
    """One-stop per-response analysis the service stores on save."""
    star = detect_star(text)
    present, mtype, band = detect_impact(text)
    return {
        "star": star,
        "star_count": sum(star.values()),
        "impact_metric_present": present,
        "impact_metric_type": mtype,
        "impact_metric_value_band": band,
        "word_count": word_count(text),
        "word_count_compliance": word_count_compliance(text, word_limit),
        "authenticity_risk_flags": authenticity_risk_flags(text),
        # Authentic-looking unless a risk flag fired (§3.19 authenticity flag).
        "authenticity_confidence_flag": not authenticity_risk_flags(text) and bool(text),
    }


# ── Aggregate inference (§4.17) ──────────────────────────────────────────────
_DRAFT_WEIGHT = {"none": 0.0, "draft": 0.5, "revised": 0.8, "final": 1.0}


def _has_text(resp: dict) -> bool:
    return bool((resp.get("response_text") or "").strip())


def _star_count(resp: dict) -> int:
    return sum(
        bool(resp.get(f"star_{k}_present"))
        for k in ("situation", "task", "action", "result", "reflection")
    )


def response_strength(resp: dict) -> float:
    """0..1 quality of a single response (STAR depth · finalization · confidence)."""
    if not _has_text(resp):
        return 0.0
    star = _star_count(resp) / 5.0
    finalize = _DRAFT_WEIGHT.get(resp.get("draft_status") or "none", 0.0)
    conf = (resp.get("confidence_self_rating") or 0) / 5.0
    # STAR depth is the spine; finalization + self-confidence round it out.
    return round(0.55 * star + 0.30 * finalize + 0.15 * conf, 3)


def interview_readiness(responses: list[dict], prompts: list[dict]) -> dict:
    """Readiness band+score over the canonical interview set (§4.14/§6 gate)."""
    by_key = {r.get("prompt_key"): r for r in responses}
    core = [k for k in CORE_INTERVIEW_KEYS if any(p.get("prompt_key") == k for p in prompts)]
    denom = core or [p["prompt_key"] for p in prompts if p.get("target_channel") == "interview"]
    if not denom:
        return {"band": "low", "score": 0, "answered": 0, "core_total": 0, "star_avg": 0.0}
    strengths = [response_strength(by_key[k]) for k in denom if k in by_key]
    answered = sum(1 for k in denom if k in by_key and _has_text(by_key[k]))
    score = round(100 * sum(strengths) / len(denom)) if denom else 0
    star_avg = (
        round(sum(_star_count(by_key[k]) for k in denom if k in by_key) / max(1, answered), 2)
        if answered
        else 0.0
    )
    band = "high" if score >= 70 else "medium" if score >= 40 else "low"
    return {
        "band": band,
        "score": score,
        "answered": answered,
        "core_total": len(denom),
        "star_avg": star_avg,
    }


# Map prompt intent_tag → competency vocabulary used by the story bank (§3.20).
_INTENT_TO_COMPETENCY: dict[str, str] = {
    "leadership": "leadership",
    "conflict": "communication",
    "failure": "resilience",
    "impact": "impact",
    "ethics": "communication",
    "learning": "analytical",
    "motivation": "initiative",
    "fit": "teamwork",
    "vision": "initiative",
    "curiosity": "analytical",
    "resilience": "resilience",
    "service": "teamwork",
    "teamwork": "teamwork",
    "communication": "communication",
    "identity": "initiative",
}

_ALL_COMPETENCIES = (
    "leadership",
    "teamwork",
    "impact",
    "resilience",
    "creativity",
    "analytical",
    "communication",
    "initiative",
)


def competency_coverage(stories: list[dict], responses: list[dict], prompts: list[dict]) -> dict:
    """Which competencies are evidenced (story bank + answered prompts) vs gaps."""
    covered: dict[str, int] = {c: 0 for c in _ALL_COMPETENCIES}
    for s in stories:
        for c in {s.get("primary_competency"), s.get("secondary_competency")}:
            if c in covered:
                covered[c] += 1
        for c in s.get("competency_tags") or []:
            if c in covered:
                covered[c] += 1
    prompt_intent = {p.get("prompt_key"): p.get("intent_tag") for p in prompts}
    for r in responses:
        if not _has_text(r):
            continue
        comp = _INTENT_TO_COMPETENCY.get(prompt_intent.get(r.get("prompt_key")) or "")
        if comp in covered:
            covered[comp] += 1
    gaps = [c for c, n in covered.items() if n == 0]
    return {"map": covered, "gaps": gaps}


def match_stories_to_prompts(
    stories: list[dict], prompts: list[dict], responses: list[dict]
) -> list[dict]:
    """Story↔prompt matching table (§4.17). Best story per still-unanswered prompt."""
    answered = {r.get("prompt_key") for r in responses if _has_text(r)}
    out: list[dict] = []
    for p in prompts:
        key = p.get("prompt_key")
        if key in answered:
            continue
        want = _INTENT_TO_COMPETENCY.get(p.get("intent_tag") or "")
        best, best_score = None, 0.0
        for s in stories:
            score = 0.0
            comps = {s.get("primary_competency"), s.get("secondary_competency")} | set(
                s.get("competency_tags") or []
            )
            if want and want in comps:
                score += 1.0
            if s.get("primary_competency") == want:
                score += 0.5
            score += 0.1 * min(3, len(s.get("competency_tags") or []))
            if score > best_score:
                best, best_score = s, score
        if best and best_score >= 1.0:
            out.append(
                {
                    "prompt_key": key,
                    "prompt_title": p.get("title"),
                    "best_story_id": str(best.get("id")),
                    "best_story_title": best.get("title"),
                    "score": round(best_score, 2),
                }
            )
    return out


def revision_priority_list(responses: list[dict], prompts: list[dict]) -> list[dict]:
    """Ordered highest-ROI edits (§4.17). Weak/under-developed answers first."""
    by_key = {p.get("prompt_key"): p for p in prompts}
    items: list[dict] = []
    for r in responses:
        if not _has_text(r):
            continue
        strength = response_strength(r)
        if strength >= 0.8:
            continue
        missing = [
            k
            for k in ("situation", "task", "action", "result", "reflection")
            if not r.get(f"star_{k}_present")
        ]
        reason_bits = []
        if missing:
            reason_bits.append("add " + "/".join(missing[:3]))
        if (r.get("draft_status") or "none") != "final":
            reason_bits.append("not finalized")
        if not r.get("impact_metric_present"):
            reason_bits.append("quantify impact")
        p = by_key.get(r.get("prompt_key")) or {}
        items.append(
            {
                "prompt_key": r.get("prompt_key"),
                "prompt_title": p.get("title"),
                "strength": strength,
                "reason": "; ".join(reason_bits) or "tighten",
            }
        )
    items.sort(key=lambda x: x["strength"])
    return items[:8]


def suggested_practice_plan(readiness: dict, coverage: dict, revision: list[dict]) -> str:
    """A short, plain-language plan (the LLM-swap-in slot)."""
    lines: list[str] = []
    band = readiness.get("band", "low")
    answered, total = readiness.get("answered", 0), readiness.get("core_total", 0)
    if band == "high":
        lines.append(
            f"You're interview-ready on {answered}/{total} core questions — "
            "polish delivery and practice aloud against the time limits."
        )
    elif band == "medium":
        lines.append(
            f"You've made solid progress ({answered}/{total} core questions). "
            "Focus next on the highest-ROI revisions below."
        )
    else:
        lines.append(
            f"Start with the core interview set — {answered}/{total} answered. "
            "Draft each using STAR (Situation · Task · Action · Result · Reflection)."
        )
    gaps = coverage.get("gaps") or []
    if gaps:
        lines.append(
            "Build a story-bank entry for: " + ", ".join(gaps[:4]) + " — these competencies "
            "have no evidence yet."
        )
    if revision:
        top = revision[0]
        lines.append(f"Quickest win: “{top.get('prompt_title')}” — {top.get('reason')}.")
    return " ".join(lines)


def coach_summary(responses: list[dict], stories: list[dict], prompts: list[dict]) -> dict:
    """The §4.17 behavioral-output bundle the summary endpoint attaches."""
    readiness = interview_readiness(responses, prompts)
    coverage = competency_coverage(stories, responses, prompts)
    matching = match_stories_to_prompts(stories, prompts, responses)
    revision = revision_priority_list(responses, prompts)
    return {
        "interview_readiness_band": readiness["band"],
        "interview_readiness_score": readiness["score"],
        "readiness_detail": readiness,
        "competency_coverage_map": coverage["map"],
        "competency_coverage_gaps": coverage["gaps"],
        "story_prompt_matching_table": matching,
        "revision_priority_list": revision,
        "suggested_practice_plan": suggested_practice_plan(readiness, coverage, revision),
    }
