"""Spec 43 §4.18 — MajorTrackCoach (major-specific inference layer).

Deterministic engine that turns a student's per-track signal subdocument
(``student_major_specific_signals.signals``) into the Spec 42 §4.18 outputs:
``major_track_fit_score``, a readiness band (CS exposes it as
``coding_readiness_band``), ``project_coverage_map``, ``skill_gap_severity``,
``specialization_match_tags``, ``suggested_artifacts_to_add``,
``suggested_bridge_plan``, and ``track_recommendation``.

Pure and deterministic — it never 5xxes (same stance as ``prompt_coach`` /
``prospect_prioritizer``). ``MajorSpecificService`` applies this overlay only
when ``ai_major_specific_v2_enabled`` is on; the raw catalog + signals are always
served regardless. The registry tier (``workhorse`` / Sonnet) documents the
future LLM swap-in (richer bridge-plan narration + per-program artifact
prioritization), which would fall back to this engine on any failure.
"""

from __future__ import annotations

from unipaith.services import major_track_catalog as cat

# A 1–5 rating at/below this is a "weak" area worth surfacing as a gap.
_WEAK_AT_OR_BELOW = 2
# A cluster/group mean at/above this counts as a demonstrated strength.
_STRONG_AT_OR_ABOVE = 3.5


def _is_filled(field: dict, value) -> bool:
    """Whether a non-rating field counts as 'answered' (evidence present)."""
    kind = field["kind"]
    if value is None:
        return False
    if kind == "bool":
        return bool(value)
    if kind == "tags":
        return isinstance(value, list) and len(value) > 0
    if kind in ("link", "text", "enum"):
        return bool(str(value).strip())
    if kind == "number":
        try:
            return float(value) > 0
        except (TypeError, ValueError):
            return False
    return value is not None


def _rating(value) -> int | None:
    """Coerce a stored value to a 1–5 int, or None if absent/invalid."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= 5 else None


def _cluster_mean(signals: dict, keys: tuple[str, ...]) -> float | None:
    vals = [r for k in keys if (r := _rating(signals.get(k))) is not None]
    return sum(vals) / len(vals) if vals else None


def fit_score(track_key: str, signals: dict) -> int:
    """0–100 demonstrated strength: 75% rating level, 25% evidence fill.

    Self-rated skill is the spine of fit; evidence (links/flags) rounds it out.
    A student who has maxed their self-ratings reaches the high band even before
    attaching every artifact — artifacts are surfaced separately as
    ``suggested_artifacts_to_add``.
    """
    fields = cat.track_fields(track_key)
    rating_vals = [
        r for k, f in fields.items() if f["kind"] == "rating_1_5" and (r := _rating(signals.get(k)))
    ]
    rating_keys = [k for k, f in fields.items() if f["kind"] == "rating_1_5"]
    evidence_keys = [k for k, f in fields.items() if f["kind"] != "rating_1_5"]

    rating_level = (sum(rating_vals) / len(rating_vals) / 5.0) if rating_vals else 0.0
    if evidence_keys:
        filled = sum(1 for k in evidence_keys if _is_filled(fields[k], signals.get(k)))
        evidence_fill = filled / len(evidence_keys)
    else:
        evidence_fill = 0.0

    if rating_keys and evidence_keys:
        score = 0.75 * rating_level + 0.25 * evidence_fill
    elif rating_keys:
        score = rating_level
    else:
        score = evidence_fill
    return round(100 * score)


def completeness(track_key: str, signals: dict) -> int:
    """0–100 share of the track's fields the student has answered."""
    fields = cat.track_fields(track_key)
    if not fields:
        return 0
    answered = 0
    for k, f in fields.items():
        if f["kind"] == "rating_1_5":
            answered += _rating(signals.get(k)) is not None
        else:
            answered += _is_filled(f, signals.get(k))
    return round(100 * answered / len(fields))


def readiness_band(score: int, complete: int) -> str:
    """high / medium / low from fit score gated by coverage (§4.18)."""
    if score >= 70 and complete >= 45:
        return "high"
    if score >= 45 and complete >= 20:
        return "medium"
    return "low"


def project_coverage_map(track_key: str, signals: dict) -> dict[str, int]:
    """Per-group depth 0–100 (the coverage radar, §4.18 project_coverage_map)."""
    schema = cat.track_schema(track_key)
    out: dict[str, int] = {}
    if not schema:
        return out
    for grp in schema["groups"]:
        rating_vals: list[int] = []
        evidence_filled = 0
        evidence_total = 0
        for f in grp["fields"]:
            v = signals.get(f["key"])
            if f["kind"] == "rating_1_5":
                r = _rating(v)
                if r is not None:
                    rating_vals.append(r)
            else:
                evidence_total += 1
                evidence_filled += _is_filled(f, v)
        if rating_vals and evidence_total:
            depth = 0.6 * (sum(rating_vals) / len(rating_vals) / 5.0) + 0.4 * (
                evidence_filled / evidence_total
            )
        elif rating_vals:
            depth = sum(rating_vals) / len(rating_vals) / 5.0
        elif evidence_total:
            depth = evidence_filled / evidence_total
        else:
            depth = 0.0
        out[grp["label"]] = round(100 * depth)
    return out


def gaps(track_key: str, signals: dict) -> list[dict]:
    """Weak/unanswered rating areas (label + value), weakest first."""
    fields = cat.track_fields(track_key)
    items: list[dict] = []
    for k, f in fields.items():
        if f["kind"] != "rating_1_5":
            continue
        r = _rating(signals.get(k))
        if r is None:
            items.append({"key": k, "label": f["label"], "value": None, "state": "unrated"})
        elif r <= _WEAK_AT_OR_BELOW:
            items.append({"key": k, "label": f["label"], "value": r, "state": "weak"})
    # Weak (rated low) before unrated; within weak, lowest first.
    items.sort(key=lambda x: (x["state"] == "unrated", x["value"] if x["value"] else 99))
    return items[:8]


def skill_gap_severity(track_key: str, signals: dict) -> str:
    """none / low / medium / high — share of rating fields weak or unrated."""
    rating_keys = cat.rating_field_keys(track_key)
    if not rating_keys:
        return "none"
    bad = 0
    for k in rating_keys:
        r = _rating(signals.get(k))
        if r is None or r <= _WEAK_AT_OR_BELOW:
            bad += 1
    frac = bad / len(rating_keys)
    if frac >= 0.5:
        return "high"
    if frac >= 0.25:
        return "medium"
    if frac > 0:
        return "low"
    return "none"


def track_recommendation(track_key: str, signals: dict) -> str | None:
    """Strongest sub-track (§4.18 track_recommendation), or None."""
    clusters = cat.recommendation_clusters(track_key)
    if not clusters:
        return None
    best, best_mean = None, 0.0
    for name, keys in clusters.items():
        m = _cluster_mean(signals, keys)
        if m is not None and m > best_mean:
            best, best_mean = name, m
    # Only recommend if the strongest cluster shows real signal.
    return best if best_mean >= _STRONG_AT_OR_ABOVE else None


def specialization_match_tags(track_key: str, signals: dict) -> list[str]:
    """Demonstrated specializations (§4.18). Clusters/groups at/above strong."""
    clusters = cat.recommendation_clusters(track_key)
    tags: list[str] = []
    if clusters:
        for name, keys in clusters.items():
            m = _cluster_mean(signals, keys)
            if m is not None and m >= _STRONG_AT_OR_ABOVE:
                tags.append(name)
        return tags
    # Tracks without sub-clusters: use group depth.
    for label, depth in project_coverage_map(track_key, signals).items():
        if depth >= 70:
            tags.append(label)
    return tags


def suggested_artifacts_to_add(track_key: str, signals: dict) -> list[str]:
    """Evidence the student should add (§4.18). Empty hint-fields → their hint."""
    fields = cat.track_fields(track_key)
    out: list[str] = []
    for field_key, hint in cat.artifact_hints(track_key).items():
        f = fields.get(field_key)
        if f and not _is_filled(f, signals.get(field_key)):
            out.append(hint)
    return out


def suggested_bridge_plan(
    track_key: str, band: str, gap_list: list[dict], artifacts: list[str]
) -> str:
    """Short plain-language plan (the LLM swap-in slot)."""
    schema = cat.track_schema(track_key)
    label = schema["label"] if schema else track_key
    lines: list[str] = []
    if band == "high":
        lines.append(f"You're well-prepared for {label}. Keep your strongest evidence current.")
    elif band == "medium":
        lines.append(
            f"You have a solid {label} foundation. Close the gaps below to reach the top band."
        )
    else:
        lines.append(
            f"Build out your {label} readiness — rate each area honestly, then target the lowest."
        )
    weak = [g["label"] for g in gap_list if g["state"] == "weak"][:2]
    unrated = [g["label"] for g in gap_list if g["state"] == "unrated"][:2]
    if weak:
        lines.append("Strengthen: " + ", ".join(weak) + ".")
    if unrated:
        lines.append("Still to assess: " + ", ".join(unrated) + ".")
    if artifacts:
        lines.append("Add evidence — " + artifacts[0])
    return " ".join(lines)


def coach_track(track_key: str, signals: dict) -> dict:
    """Full §4.18 output bundle for one track."""
    signals = signals or {}
    score = fit_score(track_key, signals)
    complete = completeness(track_key, signals)
    band = readiness_band(score, complete)
    gap_list = gaps(track_key, signals)
    artifacts = suggested_artifacts_to_add(track_key, signals)
    out = {
        "track_key": track_key,
        "major_track_fit_score": score,
        "completeness": complete,
        "readiness_band": band,
        "project_coverage_map": project_coverage_map(track_key, signals),
        "skill_gap_severity": skill_gap_severity(track_key, signals),
        "specialization_match_tags": specialization_match_tags(track_key, signals),
        "gaps": gap_list,
        "suggested_artifacts_to_add": artifacts,
        "track_recommendation": track_recommendation(track_key, signals),
        "suggested_bridge_plan": suggested_bridge_plan(track_key, band, gap_list, artifacts),
    }
    # CS exposes the readiness band under its canonical §4.18 name.
    if track_key == "cs_data_ai":
        out["coding_readiness_band"] = band
    return out


def coach_summary(tracks: list[dict]) -> dict:
    """Aggregate §4.18 across the student's active tracks.

    ``tracks`` is a list of {track_key, signals}. Returns per-track bundles plus
    a ``major_track_fit_score_per_target_track`` map and the primary (strongest)
    track for headline display.
    """
    per_track = [coach_track(t["track_key"], t.get("signals") or {}) for t in tracks]
    fit_map = {t["track_key"]: t["major_track_fit_score"] for t in per_track}
    primary = max(per_track, key=lambda t: t["major_track_fit_score"], default=None)
    return {
        "tracks": per_track,
        "major_track_fit_score_per_target_track": fit_map,
        "primary_track": primary["track_key"] if primary else None,
    }
