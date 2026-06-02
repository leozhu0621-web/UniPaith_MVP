"""Spec 43 — Major-Specific Field Catalog service.

Owns the per-(student, track) signal subdocuments
(``student_major_specific_signals``): which tracks are active (derived from the
student's major + any the student opted into), reading/writing a track's signals
(validated/coerced against the catalog, with §5 provenance on every write), and
the §4.18 inference overlay (MajorTrackCoach, flag-gated).

Every write stamps the universal record metadata (Spec 42 §5) and appends to the
provenance chain. Also exposes a thin back-compat shim for the pre-spec
``/me/major-readiness`` endpoints, now served from this one canonical store.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai import major_track_coach
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.major_specific import StudentMajorSpecificSignals
from unipaith.models.student import AcademicRecord, StudentProfile
from unipaith.services import major_track_catalog as cat

logger = logging.getLogger(__name__)

# Pre-spec 6-track scaffold names → Spec 43 track_keys (back-compat shim).
_LEGACY_TO_KEY: dict[str, str] = {
    "cs": "cs_data_ai",
    "engineering": "engineering",
    "business": "business",
    "health": "health",
    "arts": "arts_design",
    "humanities": "humanities_social_sciences",
}
_KEY_TO_LEGACY: dict[str, str] = {v: k for k, v in _LEGACY_TO_KEY.items()}


def _now() -> datetime:
    return datetime.now(UTC)


def _prov(event: str, actor: str = "student") -> dict:
    return {"event": event, "timestamp": _now().isoformat(), "actor": actor}


def _coerce_signals(track_key: str, raw: dict) -> dict:
    """Validate/coerce a {field_key: value} dict against the track schema.

    Out-of-range ratings, off-vocabulary enums, and unknown keys are dropped
    (never 422'd — the form stays forgiving, Spec 43 §1). Returns a clean dict
    safe to persist as JSONB.
    """
    fields = cat.track_fields(track_key)
    out: dict = {}
    for key, value in (raw or {}).items():
        f = fields.get(key)
        if f is None or value is None:
            continue
        kind = f["kind"]
        if kind == "rating_1_5":
            try:
                n = int(value)
            except (TypeError, ValueError):
                continue
            if 1 <= n <= 5:
                out[key] = n
        elif kind == "bool":
            out[key] = bool(value)
        elif kind == "number":
            try:
                n = float(value)
            except (TypeError, ValueError):
                continue
            if n >= 0:
                # Keep ints clean (no trailing .0 in JSON).
                out[key] = int(n) if n.is_integer() else n
        elif kind == "enum":
            if isinstance(value, str) and value in f.get("options", []):
                out[key] = value
        elif kind == "tags":
            if isinstance(value, list):
                out[key] = [str(v).strip() for v in value if str(v).strip()][:50]
        elif kind in ("link", "text"):
            if isinstance(value, str) and value.strip():
                out[key] = value.strip()[:2000]
    return out


class MajorSpecificService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _profile(self, user_id: UUID) -> StudentProfile:
        prof = await self.db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
        if prof is None:
            raise NotFoundException("Student profile not found")
        return prof

    async def _suggested_tracks(self, student_id: UUID) -> list[str]:
        """track_key(s) inferred from the student's stated major (Spec 43 §1).

        The de-facto major signal in the existing MVP is
        ``AcademicRecord.field_of_study`` (current/most-recent program); we union
        the inference across the student's records so dual-field students get all
        relevant tracks. These are only *suggestions* — the student can activate
        any track manually.
        """
        rows = (
            await self.db.execute(
                select(AcademicRecord.field_of_study)
                .where(AcademicRecord.student_id == student_id)
                .order_by(AcademicRecord.is_current.desc(), AcademicRecord.created_at.desc())
            )
        ).all()
        hits: set[str] = set()
        for (field_of_study,) in rows:
            hits.update(cat.infer_tracks_from_major(field_of_study))
        return [k for k in cat.TRACK_KEYS if k in hits]

    async def _rows(self, student_id: UUID) -> list[StudentMajorSpecificSignals]:
        stmt = (
            select(StudentMajorSpecificSignals)
            .where(StudentMajorSpecificSignals.student_id == student_id)
            .order_by(StudentMajorSpecificSignals.updated_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ── Catalog ────────────────────────────────────────────────────────────────
    async def get_catalog(self, user_id: UUID) -> dict:
        prof = await self._profile(user_id)
        return {
            "tracks": cat.catalog(),
            "suggested_tracks": await self._suggested_tracks(prof.id),
        }

    # ── Tracks (read) ──────────────────────────────────────────────────────────
    def _row_out(self, row: StudentMajorSpecificSignals, *, with_coach: bool) -> dict:
        schema = cat.track_schema(row.track_key)
        out = {
            "track_key": row.track_key,
            "label": schema["label"] if schema else row.track_key,
            "signals": row.signals or {},
            "source": row.source,
            "confidence": row.confidence,
            "record_version": row.record_version,
            "updated_at": row.updated_at,
            "coach": None,
        }
        if with_coach:
            try:
                out["coach"] = major_track_coach.coach_track(row.track_key, row.signals or {})
            except Exception:  # pragma: no cover - engine is pure
                logger.exception("major_track_coach failed for %s; serving raw", row.track_key)
        return out

    async def get_tracks(self, user_id: UUID) -> dict:
        prof = await self._profile(user_id)
        rows = await self._rows(prof.id)
        with_coach = settings.ai_major_specific_v2_enabled
        return {
            "active_tracks": [r.track_key for r in rows],
            "suggested_tracks": await self._suggested_tracks(prof.id),
            "tracks": [self._row_out(r, with_coach=with_coach) for r in rows],
        }

    # ── Tracks (write) ───────────────────────────────────────────────────────────
    async def upsert_track(self, user_id: UUID, track_key: str, raw_signals: dict) -> dict:
        if not cat.is_valid_track(track_key):
            raise BadRequestException(f"Unknown track: {track_key}")
        prof = await self._profile(user_id)
        cleaned = _coerce_signals(track_key, raw_signals)

        row = await self.db.scalar(
            select(StudentMajorSpecificSignals).where(
                StudentMajorSpecificSignals.student_id == prof.id,
                StudentMajorSpecificSignals.track_key == track_key,
            )
        )
        if row is None:
            row = StudentMajorSpecificSignals(
                student_id=prof.id,
                track_key=track_key,
                signals={},
                source="student-typed",
                confidence=95,
                record_version=0,
                provenance_chain=[],
            )
            self.db.add(row)
            event = "track_created"
        else:
            event = "track_updated"

        row.signals = cleaned
        # §5 — structured student-typed self-ratings → confidence 95 (§5 rules).
        row.source = "student-typed"
        row.confidence = 95 if cleaned else 0
        row.record_version = (row.record_version or 0) + 1
        row.value_normalized = {"answered_fields": len(cleaned)}
        row.provenance_chain = list(row.provenance_chain or []) + [_prov(event)]

        await self.db.flush()
        await self.db.refresh(row)
        return self._row_out(row, with_coach=settings.ai_major_specific_v2_enabled)

    # ── Summary (§4.18) ────────────────────────────────────────────────────────
    async def summary(self, user_id: UUID) -> dict:
        prof = await self._profile(user_id)
        rows = await self._rows(prof.id)
        out: dict = {
            "active_track_count": len(rows),
            "inference_enabled": settings.ai_major_specific_v2_enabled,
        }
        if settings.ai_major_specific_v2_enabled and rows:
            try:
                overlay = major_track_coach.coach_summary(
                    [{"track_key": r.track_key, "signals": r.signals or {}} for r in rows]
                )
                out.update(overlay)
            except Exception:  # pragma: no cover - engine is pure
                logger.exception("major_track_coach summary failed; serving counts")
        return out

    # ── Legacy /me/major-readiness shim (Spec 43 supersede) ──────────────────────
    async def list_legacy(self, user_id: UUID) -> list[dict]:
        prof = await self._profile(user_id)
        rows = await self._rows(prof.id)
        return [
            {
                "id": r.id,
                "student_id": r.student_id,
                "track": _KEY_TO_LEGACY.get(r.track_key, r.track_key),
                "readiness_data": r.signals or {},
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in rows
        ]

    async def upsert_legacy(self, user_id: UUID, track: str, readiness_data: dict) -> dict:
        track_key = _LEGACY_TO_KEY.get(track, track)
        if not cat.is_valid_track(track_key):
            raise BadRequestException(f"Unknown track: {track}")
        prof = await self._profile(user_id)
        row = await self.db.scalar(
            select(StudentMajorSpecificSignals).where(
                StudentMajorSpecificSignals.student_id == prof.id,
                StudentMajorSpecificSignals.track_key == track_key,
            )
        )
        if row is None:
            row = StudentMajorSpecificSignals(
                student_id=prof.id,
                track_key=track_key,
                signals={},
                source="student-typed",
                confidence=95,
                record_version=0,
                provenance_chain=[],
            )
            self.db.add(row)
        # Legacy path stores the blob verbatim (no catalog coercion) to preserve
        # its raw-JSON contract; new endpoints coerce against the catalog.
        row.signals = dict(readiness_data or {})
        row.source = "student-typed"
        row.confidence = 95 if row.signals else 0
        row.record_version = (row.record_version or 0) + 1
        row.provenance_chain = list(row.provenance_chain or []) + [_prov("legacy_upsert")]
        await self.db.flush()
        await self.db.refresh(row)
        return {
            "id": row.id,
            "student_id": row.student_id,
            "track": _KEY_TO_LEGACY.get(row.track_key, row.track_key),
            "readiness_data": row.signals or {},
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
