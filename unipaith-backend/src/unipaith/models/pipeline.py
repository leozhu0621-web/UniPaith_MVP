"""Pipeline models.

Tracks the state of the continuous three-stage pipeline:
- PipelineStageSnapshot: per-stage status, throughput, queue depth, worker heartbeat
- PipelineConfig: live-editable key-value config (persists across restarts)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin


class PipelineStageSnapshot(TimestampMixin, Base):
    __tablename__ = "pipeline_stage_snapshots"

    stage: Mapped[str] = mapped_column(String(50), primary_key=True)

    status: Mapped[str] = mapped_column(String(50), default="off")
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items_processed_total: Mapped[int] = mapped_column(Integer, default=0)
    items_processed_hour: Mapped[int] = mapped_column(Integer, default=0)
    hour_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    queue_depth: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)

    extra_json: Mapped[dict | None] = mapped_column(JSONB)

    worker_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_hostname: Mapped[str | None] = mapped_column(String(255))

    budget_spent_this_hour: Mapped[float] = mapped_column(Float, default=0.0)
    budget_per_hour: Mapped[float] = mapped_column(Float, default=5.0)


class PipelineConfig(TimestampMixin, Base):
    __tablename__ = "pipeline_configs"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value_json: Mapped[dict | None] = mapped_column(JSONB)
    description: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (Index("ix_pipeline_configs_key", "key"),)
