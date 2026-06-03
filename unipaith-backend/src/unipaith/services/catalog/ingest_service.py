"""Spec 69 §3-§6 — deterministic program catalog ingestion.

Takes program rows (from a `program_catalog` upload §2, a crawl §3, or editorial
§7) and writes them into the Program catalog with normalization (§4), stable
identity + provenance + freshness (§6), and authority precedence (§3/§7,
first-party-wins): institution-reported program data is never overwritten by a
crawl — a lower-authority source that would change a higher-authority value is
skipped (routed to review in the ops queue, `60` §8/§9). Idempotent — re-ingesting
the same program updates in place (keyed on external_id or normalized name), so a
re-crawl never duplicates and only bumps `feature_version` on a real change.

Deterministic by default. The LLM crawl-extraction path (§3) and embedding-based
dedup (§5) are eval-gated follow-ups behind `ai_catalog_ingestion_v2_enabled`;
this rule-based spine is what they layer onto and the never-5xx floor.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Program
from unipaith.services.crawler.normalizer import normalize_cip

# §3/§7 authority — higher wins; institution-reported is the ceiling. Mirrors
# crawler.enrichment.authority_rank, extended with the `editorial` source (§7:
# editorial sits above low-trust crawl, below institution first-party).
CATALOG_SOURCE_AUTHORITY: dict[str, int] = {
    "crawled": 1,
    "corroborated": 2,
    "editorial": 3,
    "first_party": 4,  # institution-uploaded (program_catalog dataset)
    "institution_verified": 5,  # institution claim & verified
}

_DEGREE_MAP = {
    "ms": "masters",
    "msc": "masters",
    "ma": "masters",
    "m.s.": "masters",
    "meng": "masters",
    "mba": "masters",
    "sm": "masters",  # MIT "Master of Science"
    "scm": "masters",
    "march": "masters",  # Master of Architecture
    "mcp": "masters",  # Master in City Planning
    "mpp": "masters",  # Master of Public Policy
    "mpa": "masters",
    "med": "masters",  # Master of Education
    "llm": "masters",
    "master": "masters",
    "master's": "masters",
    "masters": "masters",
    "bs": "bachelors",
    "ba": "bachelors",
    "bsc": "bachelors",
    "bachelor": "bachelors",
    "bachelor's": "bachelors",
    "bachelors": "bachelors",
    "phd": "doctoral",
    "ph.d.": "doctoral",
    "scd": "doctoral",  # Doctor of Science
    "edd": "doctoral",
    "doctoral": "doctoral",
    "doctorate": "doctoral",
    "certificate": "certificate",
    "cert": "certificate",
    "professional": "professional",
    "jd": "professional",
    "md": "professional",
}

_MODALITY_MAP = {
    "in person": "in_person",
    "in-person": "in_person",
    "on campus": "in_person",
    "on-campus": "in_person",
    "onsite": "in_person",
    "campus": "in_person",
    "online": "online",
    "remote": "online",
    "distance": "online",
    "hybrid": "hybrid",
    "blended": "hybrid",
}

# Fields whose normalized value is compared old-vs-new to decide a "material
# change" (§6) — only those bump feature_version (the rationale/match cache key).
_MATERIAL_FIELDS = ("degree_type", "delivery_format", "tuition", "cip_code", "description_text")


def normalize_degree_type(raw: str | None) -> str | None:
    if not raw:
        return None
    return _DEGREE_MAP.get(raw.strip().lower(), raw.strip().lower())


def normalize_modality(raw: str | None) -> str | None:
    if not raw:
        return None
    return _MODALITY_MAP.get(raw.strip().lower())


def catalog_authority(source: str | None) -> int:
    return CATALOG_SOURCE_AUTHORITY.get(source or "", 0)


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "program"


def _stable_slug(institution_id: UUID, external_id: str | None, name: str) -> str:
    """Deterministic, collision-resistant slug — same program ⇒ same slug
    (idempotent). Discriminator hashes the canonical identity so distinct
    programs never collide on the unique slug index (§5/§8)."""
    disc = hashlib.sha1(f"{institution_id}:{external_id or name.lower()}".encode()).hexdigest()[:6]
    return f"{_slugify(name)[:170]}-{disc}"


def _coerce_int(value: object) -> int | None:
    try:
        return int(float(value))  # "50000" / "50000.0" / 50000 all work
    except (ValueError, TypeError):
        return None


class CatalogIngestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ingest_programs(
        self,
        institution_id: UUID,
        rows: list[dict],
        *,
        source: str = "first_party",
        source_url: str | None = None,
        school_id: UUID | None = None,
    ) -> dict:
        """Ingest program rows for one institution. Returns a summary
        {created, updated, skipped} (§9 acceptance: many programs, deduped,
        provenance-stamped, first-party-wins)."""
        created = updated = skipped = 0
        for row in rows:
            name = (row.get("program_name") or "").strip()
            if not name:
                skipped += 1
                continue
            external_id = (row.get("external_id") or "").strip() or None
            existing = await self._resolve(institution_id, external_id, name)

            if existing is not None and catalog_authority(
                existing.catalog_source
            ) > catalog_authority(source):
                # First-party-wins (§3/§7): never overwrite higher-authority data
                # with a lower source — the conflict routes to review, not a write.
                skipped += 1
                continue

            if existing is None:
                prog = Program(
                    institution_id=institution_id,
                    program_name=name,
                    degree_type=normalize_degree_type(row.get("degree_type")) or "unknown",
                )
                self.db.add(prog)
                self._apply(prog, row, source, source_url, external_id, name, school_id)
                prog.feature_version = 1
                created += 1
            else:
                before = {f: getattr(existing, f) for f in _MATERIAL_FIELDS}
                self._apply(existing, row, source, source_url, external_id, name, school_id)
                if any(getattr(existing, f) != before[f] for f in _MATERIAL_FIELDS):
                    existing.feature_version = (existing.feature_version or 1) + 1
                updated += 1
            await self.db.flush()
        return {"created": created, "updated": updated, "skipped": skipped}

    async def _resolve(
        self, institution_id: UUID, external_id: str | None, name: str
    ) -> Program | None:
        """Resolve to an existing program — external_id first (stable), then
        normalized name within the institution (§2 program-ID normalization)."""
        if external_id:
            res = await self.db.execute(
                select(Program).where(
                    Program.institution_id == institution_id,
                    Program.external_id == external_id,
                )
            )
            row = res.scalar_one_or_none()
            if row is not None:
                return row
        res = await self.db.execute(
            select(Program).where(
                Program.institution_id == institution_id,
                func.lower(Program.program_name) == name.lower(),
            )
        )
        return res.scalar_one_or_none()

    def _apply(
        self,
        prog: Program,
        row: dict,
        source: str,
        source_url: str | None,
        external_id: str | None,
        name: str,
        school_id: UUID | None,
    ) -> None:
        prog.program_name = name
        dt = normalize_degree_type(row.get("degree_type"))
        if dt:
            prog.degree_type = dt
        modality = normalize_modality(row.get("delivery_format"))
        if modality:
            prog.delivery_format = modality
        if row.get("cip_code"):
            prog.cip_code = normalize_cip(str(row["cip_code"]))
        if row.get("tuition") is not None:
            tuition = _coerce_int(row["tuition"])
            if tuition is not None:
                prog.tuition = tuition
        if row.get("duration_months") is not None:
            dur = _coerce_int(row["duration_months"])
            if dur is not None:
                prog.duration_months = dur
        if row.get("description"):
            prog.description_text = str(row["description"])
        if school_id is not None:
            prog.school_id = school_id
        # Stable identity + provenance + freshness (§6).
        if external_id:
            prog.external_id = external_id
        if not prog.slug:
            prog.slug = _stable_slug(prog.institution_id, external_id, name)
        prog.catalog_source = source
        prog.source_url = source_url
        prog.last_ingested_at = datetime.now(UTC)
        prog.is_published = True
