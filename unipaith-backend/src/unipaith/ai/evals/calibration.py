"""Spec 62 §4 — the judge-calibration record (the trust foundation).

§4 requires the LLM-judge be calibrated to humans (≥85–90% agreement) before it
is trusted, and that **the number is recorded** and re-checked on model/rubric
change. This module is that record, per consumer, read from
``fixtures/calibration/<consumer>.json`` (or a sensible baseline default).

Honest by design: the agreement figure ships ``null`` (a live human-labeling pass
is the expert-hours staffing item §13 names, shared with 60/61), so the surface
marks judge calibration **partial** rather than asserting a number nobody
measured. What *is* recorded and live: which model judges, whether it is
independent of the system under test (§4 "avoid self-grading"), the target, and
the fact that deterministic checks gate first so a missing judge never silently
passes a case.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

_CALIBRATION_DIR = Path(__file__).parent / "fixtures" / "calibration"


@dataclass(frozen=True)
class CalibrationRecord:
    consumer: str
    judge_model: str
    judge_family: str
    system_under_test: str
    independent: bool
    agreement: float | None
    target_agreement: float
    labeled_case_count: int
    status: str  # "calibrated" | "baseline"
    note: str

    @property
    def meets_target(self) -> bool:
        return self.agreement is not None and self.agreement >= self.target_agreement

    def as_dict(self) -> dict:
        return {
            "consumer": self.consumer,
            "judge_model": self.judge_model,
            "judge_family": self.judge_family,
            "system_under_test": self.system_under_test,
            "independent": self.independent,
            "agreement": self.agreement,
            "target_agreement": self.target_agreement,
            "labeled_case_count": self.labeled_case_count,
            "status": self.status,
            "meets_target": self.meets_target,
            "note": self.note,
        }


def _default(consumer: str) -> CalibrationRecord:
    return CalibrationRecord(
        consumer=consumer,
        judge_model="haiku",
        judge_family="claude",
        system_under_test="unknown",
        independent=False,
        agreement=None,
        target_agreement=0.85,
        labeled_case_count=0,
        status="baseline",
        note="No calibration file on disk; baseline defaults.",
    )


@cache
def calibration_for(consumer: str) -> CalibrationRecord:
    """The calibration record for a consumer. Cached — files are static at runtime."""
    path = _CALIBRATION_DIR / f"{consumer}.json"
    if not path.is_file():
        return _default(consumer)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return CalibrationRecord(
        consumer=raw.get("consumer", consumer),
        judge_model=raw.get("judge_model", "haiku"),
        judge_family=raw.get("judge_family", "claude"),
        system_under_test=raw.get("system_under_test", "unknown"),
        independent=bool(raw.get("independent", False)),
        agreement=raw.get("agreement"),
        target_agreement=float(raw.get("target_agreement", 0.85)),
        labeled_case_count=int(raw.get("labeled_case_count", 0)),
        status=raw.get("status", "baseline"),
        note=raw.get("note", ""),
    )
