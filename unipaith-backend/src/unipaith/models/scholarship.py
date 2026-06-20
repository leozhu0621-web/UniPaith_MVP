"""External scholarships catalog — Spec 2026-06-14 (Resources › Financial).

9,500 real awards scraped from the U.S. Dept of Labor's CareerOneStop
Scholarship Finder, seeded from ``data/scholarships.json``. ``external_id``
is the CareerOneStop detail id (a numeric string) and drives an idempotent
re-seed.

Honesty (spec §Data): ``award_amount`` and ``deadline`` are verbatim source
text kept as strings — never parsed into false precision. No eligibility is
invented.

Naming note: the table is ``external_scholarships`` (not ``scholarships``)
because Spec 60's ``models/reference.py::Scholarship`` already owns the
``scholarships`` table (institution/program-linked reference awards consumed by
``financial_fit`` / ``uni_knowledge``). This is the distinct *external*
CareerOneStop catalog, so it gets its own table to avoid a SQLAlchemy
metadata collision.
"""

from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Scholarship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An external scholarship award from CareerOneStop (Spec 2026-06-14)."""

    __tablename__ = "external_scholarships"
    __table_args__ = (
        Index("ix_external_scholarships_external_id", "external_id", unique=True),
        Index("ix_external_scholarships_level_of_study", "level_of_study"),
    )

    external_id: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(500))
    purpose: Mapped[str | None] = mapped_column(Text)
    level_of_study: Mapped[str | None] = mapped_column(String(300))
    award_type: Mapped[str | None] = mapped_column(String(120))
    # Verbatim source text (e.g. "$1,000 $5,000") — never parsed (spec §Data).
    award_amount: Mapped[str | None] = mapped_column(String(200))
    # Verbatim month text (e.g. "November") — never parsed (spec §Data).
    deadline: Mapped[str | None] = mapped_column(String(120))
    url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(60), nullable=False, default="careeronestop")
