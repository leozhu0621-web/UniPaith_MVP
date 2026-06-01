"""Spec 24 — institution dataset upload, validation, versioning."""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.institution import (
    InstitutionDataset,
    InstitutionDatasetMappingTemplate,
    InstitutionDatasetVersion,
    Program,
)
from unipaith.services.audit_service import AuditService

REQUIRED_FIELDS: dict[str, list[str]] = {
    "prospect_list": ["email"],
    "admissions_history": ["student_email", "program_name", "decision"],
    "outcomes_summary": ["program_name", "graduation_year"],
}

PRIMARY_KEY_FIELDS: dict[str, list[str]] = {
    "prospect_list": ["email"],
    "admissions_history": ["student_email", "program_name", "application_date"],
    "outcomes_summary": ["program_name", "graduation_year"],
}

DATE_FIELDS = frozenset(
    {"application_date", "program_start_date", "graduation_year", "coverage_start", "coverage_end"}
)

USAGE_CONSUMERS: dict[str, list[str]] = {
    "marketing": ["campaigns"],
    "admissions": ["matching", "pipeline"],
    "analytics": ["analytics"],
    "all": ["matching", "campaigns", "analytics"],
}


def _read_dataset_content(s3_key: str) -> str:
    if settings.s3_local_mode:
        from pathlib import Path

        local_path = Path(settings.s3_local_path) / s3_key
        if not local_path.exists():
            return ""
        return local_path.read_text(encoding="utf-8", errors="replace")

    import boto3

    client = boto3.client("s3", region_name=settings.aws_region)
    obj = client.get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    return obj["Body"].read().decode("utf-8", errors="replace")


def _write_dataset_content(s3_key: str, content: str) -> None:
    if settings.s3_local_mode:
        from pathlib import Path

        local_path = Path(settings.s3_local_path) / s3_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(content, encoding="utf-8")
        return

    import boto3

    client = boto3.client("s3", region_name=settings.aws_region)
    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Body=content.encode("utf-8"),
        ContentType="text/csv",
    )


def _parse_rows(content: str) -> tuple[list[str], list[dict[str, str]]]:
    if not content.strip():
        return [], []
    sample = content[:4096]
    delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    columns = list(reader.fieldnames or [])
    rows = [dict(row) for row in reader]
    return columns, rows


def _mapped_row(raw: dict[str, str], column_mapping: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for src, dst in column_mapping.items():
        if dst and src in raw:
            out[dst] = (raw.get(src) or "").strip()
    return out


def _parse_date_value(value: str) -> bool:
    if not value or not value.strip():
        return False
    v = value.strip()
    if re.fullmatch(r"\d{4}", v):
        return True
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            datetime.strptime(v, fmt)
            return True
        except ValueError:
            continue
    return False


def validate_dataset_rows(
    *,
    dataset_type: str,
    rows: list[dict[str, str]],
    column_mapping: dict[str, str],
    program_names: list[str],
) -> dict[str, Any]:
    """Build Spec §7 validation report from mapped rows (1-based row indices)."""
    missing_required: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    invalid_dates: list[dict[str, Any]] = []
    unmappable_programs: list[dict[str, Any]] = []

    required = REQUIRED_FIELDS.get(dataset_type, [])
    pk_fields = PRIMARY_KEY_FIELDS.get(dataset_type, [])
    program_lookup = {n.lower(): n for n in program_names}
    seen_keys: dict[tuple[str, ...], int] = {}

    for idx, raw in enumerate(rows, start=2):  # header is row 1
        mapped = _mapped_row(raw, column_mapping)
        for field in required:
            if not (mapped.get(field) or "").strip():
                missing_required.append({"row": idx, "field": field})

        for field, value in mapped.items():
            if field in DATE_FIELDS and value and not _parse_date_value(value):
                invalid_dates.append({"row": idx, "field": field, "value": value})

        if dataset_type in ("admissions_history", "outcomes_summary"):
            pname = (mapped.get("program_name") or "").strip()
            if pname and pname.lower() not in program_lookup:
                suggestions = [
                    n
                    for n in program_names
                    if pname.lower() in n.lower() or n.lower() in pname.lower()
                ][:3]
                unmappable_programs.append({"row": idx, "value": pname, "suggestions": suggestions})

        if pk_fields:
            key_parts = tuple((mapped.get(f) or "").strip().lower() for f in pk_fields)
            if any(key_parts):
                if key_parts in seen_keys:
                    duplicates.append({"row": idx, "duplicate_of_row": seen_keys[key_parts]})
                else:
                    seen_keys[key_parts] = idx

    return {
        "missing_required": missing_required,
        "duplicates": duplicates,
        "invalid_dates": invalid_dates,
        "unmappable_programs": unmappable_programs,
        "error_count": (
            len(missing_required) + len(duplicates) + len(invalid_dates) + len(unmappable_programs)
        ),
    }


def filter_valid_rows(
    rows: list[dict[str, str]],
    column_mapping: dict[str, str],
    report: dict[str, Any],
) -> list[dict[str, str]]:
    """Drop rows referenced in validation issues when skip_invalid_rows is true."""
    bad_rows = set()
    for section in ("missing_required", "duplicates", "invalid_dates", "unmappable_programs"):
        for item in report.get(section, []):
            if "row" in item:
                bad_rows.add(item["row"])
    kept: list[dict[str, str]] = []
    for idx, raw in enumerate(rows, start=2):
        if idx not in bad_rows:
            kept.append(raw)
    return kept


def rows_to_csv(columns: list[str], rows: list[dict[str, str]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def column_histogram(rows: list[dict[str, str]], columns: list[str]) -> dict[str, dict[str, int]]:
    hist: dict[str, dict[str, int]] = {}
    for col in columns:
        counts: dict[str, int] = {}
        for row in rows[:500]:
            val = (row.get(col) or "").strip() or "(empty)"
            if len(val) > 40:
                val = val[:37] + "..."
            counts[val] = counts.get(val, 0) + 1
        top = dict(sorted(counts.items(), key=lambda x: -x[1])[:8])
        hist[col] = top
    return hist


class DatasetUploadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _program_names(self, institution_id: UUID) -> list[str]:
        result = await self.db.execute(
            select(Program.program_name).where(Program.institution_id == institution_id)
        )
        return [r[0] for r in result.all() if r[0]]

    async def _snapshot_version(
        self,
        dataset: InstitutionDataset,
        *,
        changes_summary: dict[str, int],
        validation_report: dict | None,
        user_id: UUID,
    ) -> None:
        version = InstitutionDatasetVersion(
            dataset_id=dataset.id,
            version_number=dataset.version,
            s3_key=dataset.s3_key,
            file_name=dataset.file_name,
            row_count=dataset.row_count,
            column_mapping=dataset.column_mapping,
            changes_summary=changes_summary,
            validation_report=validation_report,
            uploaded_by=user_id,
        )
        self.db.add(version)
        await self.db.flush()

    async def confirm_upload(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        user_id: UUID,
        *,
        column_mapping: dict[str, str] | None,
        skip_invalid_rows: bool = False,
        save_template: bool = False,
        template_name: str | None = None,
    ) -> tuple[InstitutionDataset, dict[str, Any]]:
        dataset = await self._get_dataset(institution_id, dataset_id)
        if column_mapping:
            dataset.column_mapping = column_mapping

        content = _read_dataset_content(dataset.s3_key)
        columns, rows = _parse_rows(content)
        mapping = dataset.column_mapping or {}
        if not mapping and columns:
            raise BadRequestException("Column mapping is required before confirming upload")

        program_names = await self._program_names(institution_id)
        report = validate_dataset_rows(
            dataset_type=dataset.dataset_type,
            rows=rows,
            column_mapping=mapping,
            program_names=program_names,
        )

        if report["error_count"] > 0 and not skip_invalid_rows:
            dataset.validation_errors = report
            dataset.status = "failed"
            await self.db.flush()
            return dataset, report

        if report["error_count"] > 0 and skip_invalid_rows:
            rows = filter_valid_rows(rows, mapping, report)
            content = rows_to_csv(columns, rows)
            _write_dataset_content(dataset.s3_key, content)

        dataset.row_count = len(rows)
        dataset.validation_errors = report if report["error_count"] else None
        dataset.status = "processed"
        dataset.version = (dataset.version or 0) + 1
        await self._snapshot_version(
            dataset,
            changes_summary={
                "added": len(rows),
                "modified": 0,
                "invalidated": report["error_count"],
            },
            validation_report=report,
            user_id=user_id,
        )
        await self.db.flush()
        await self.db.refresh(dataset)

        if save_template and mapping and template_name:
            await self.save_mapping_template(
                institution_id,
                template_name=template_name,
                dataset_type=dataset.dataset_type,
                column_mapping=mapping,
            )

        return dataset, report

    async def get_preview(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        *,
        limit: int = 100,
    ) -> dict[str, Any]:
        dataset = await self._get_dataset(institution_id, dataset_id)
        content = _read_dataset_content(dataset.s3_key)
        columns, rows = _parse_rows(content)
        total = len(rows)
        if dataset.row_count is None:
            dataset.row_count = total
            await self.db.flush()

        preview_rows = rows[:limit]
        return {
            "columns": columns,
            "rows": preview_rows,
            "total_rows": total,
            "column_histogram": column_histogram(preview_rows, columns) if preview_rows else {},
        }

    async def replace_or_append_file(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        user_id: UUID,
        *,
        new_s3_key: str,
        new_file_name: str,
        mode: str,
        column_mapping: dict[str, str] | None = None,
        skip_invalid_rows: bool = False,
    ) -> tuple[InstitutionDataset, dict[str, Any]]:
        dataset = await self._get_dataset(institution_id, dataset_id)
        old_content = _read_dataset_content(dataset.s3_key)
        new_content = _read_dataset_content(new_s3_key)
        old_cols, old_rows = _parse_rows(old_content)
        new_cols, new_rows = _parse_rows(new_content)

        if mode == "append":
            merged_cols = list(dict.fromkeys(old_cols + [c for c in new_cols if c not in old_cols]))
            merged_rows = old_rows + new_rows
            content = rows_to_csv(merged_cols, merged_rows)
            _write_dataset_content(dataset.s3_key, content)
            added, modified = len(new_rows), 0
        else:
            content = new_content
            _write_dataset_content(dataset.s3_key, content)
            dataset.file_name = new_file_name
            added, modified = len(new_rows), 0

        if new_s3_key != dataset.s3_key:
            from unipaith.core.s3 import S3Client

            S3Client().delete_object(new_s3_key)

        if column_mapping:
            dataset.column_mapping = column_mapping

        columns, rows = _parse_rows(content)
        mapping = dataset.column_mapping or {}
        program_names = await self._program_names(institution_id)
        report = validate_dataset_rows(
            dataset_type=dataset.dataset_type,
            rows=rows,
            column_mapping=mapping,
            program_names=program_names,
        )

        if report["error_count"] > 0 and not skip_invalid_rows:
            dataset.validation_errors = report
            dataset.status = "failed"
            await self.db.flush()
            return dataset, report

        if report["error_count"] > 0 and skip_invalid_rows:
            rows = filter_valid_rows(rows, mapping, report)
            content = rows_to_csv(columns, rows)
            _write_dataset_content(dataset.s3_key, content)

        dataset.row_count = len(rows)
        dataset.validation_errors = report if report["error_count"] else None
        dataset.status = "processed"
        dataset.version = (dataset.version or 0) + 1
        await self._snapshot_version(
            dataset,
            changes_summary={
                "added": added,
                "modified": modified,
                "invalidated": report["error_count"],
            },
            validation_report=report,
            user_id=user_id,
        )
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset, report

    async def list_versions(
        self, institution_id: UUID, dataset_id: UUID
    ) -> list[InstitutionDatasetVersion]:
        await self._get_dataset(institution_id, dataset_id)
        result = await self.db.execute(
            select(InstitutionDatasetVersion)
            .where(InstitutionDatasetVersion.dataset_id == dataset_id)
            .order_by(InstitutionDatasetVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def rollback_version(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        user_id: UUID,
    ) -> InstitutionDataset:
        dataset = await self._get_dataset(institution_id, dataset_id)
        result = await self.db.execute(
            select(InstitutionDatasetVersion).where(
                InstitutionDatasetVersion.id == version_id,
                InstitutionDatasetVersion.dataset_id == dataset_id,
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            raise NotFoundException("Version not found")

        content = _read_dataset_content(version.s3_key)
        _write_dataset_content(dataset.s3_key, content)
        dataset.file_name = version.file_name
        dataset.row_count = version.row_count
        dataset.column_mapping = version.column_mapping
        dataset.version = (dataset.version or 0) + 1
        dataset.status = "processed"
        dataset.validation_errors = None
        await self._snapshot_version(
            dataset,
            changes_summary={"added": 0, "modified": 0, "invalidated": 0},
            validation_report={"rollback_from_version": version.version_number},
            user_id=user_id,
        )
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset

    async def delete_dataset(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        user_id: UUID,
    ) -> None:
        dataset = await self._get_dataset(institution_id, dataset_id)
        from unipaith.core.s3 import S3Client

        S3Client().delete_object(dataset.s3_key)
        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=user_id,
            action="dataset_deleted",
            entity_type="institution_dataset",
            entity_id=str(dataset.id),
            description=f"Deleted dataset {dataset.dataset_name}",
            old_value={"dataset_name": dataset.dataset_name, "dataset_type": dataset.dataset_type},
        )
        await self.db.delete(dataset)
        await self.db.flush()

    async def list_mapping_templates(
        self, institution_id: UUID, dataset_type: str | None = None
    ) -> list[InstitutionDatasetMappingTemplate]:
        stmt = select(InstitutionDatasetMappingTemplate).where(
            InstitutionDatasetMappingTemplate.institution_id == institution_id
        )
        if dataset_type:
            stmt = stmt.where(InstitutionDatasetMappingTemplate.dataset_type == dataset_type)
        result = await self.db.execute(
            stmt.order_by(InstitutionDatasetMappingTemplate.updated_at.desc())
        )
        return list(result.scalars().all())

    async def save_mapping_template(
        self,
        institution_id: UUID,
        *,
        template_name: str,
        dataset_type: str,
        column_mapping: dict[str, str],
    ) -> InstitutionDatasetMappingTemplate:
        result = await self.db.execute(
            select(InstitutionDatasetMappingTemplate).where(
                InstitutionDatasetMappingTemplate.institution_id == institution_id,
                InstitutionDatasetMappingTemplate.template_name == template_name,
                InstitutionDatasetMappingTemplate.dataset_type == dataset_type,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.column_mapping = column_mapping
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        tpl = InstitutionDatasetMappingTemplate(
            institution_id=institution_id,
            template_name=template_name,
            dataset_type=dataset_type,
            column_mapping=column_mapping,
        )
        self.db.add(tpl)
        await self.db.flush()
        await self.db.refresh(tpl)
        return tpl

    async def _get_dataset(self, institution_id: UUID, dataset_id: UUID) -> InstitutionDataset:
        result = await self.db.execute(
            select(InstitutionDataset).where(
                InstitutionDataset.id == dataset_id,
                InstitutionDataset.institution_id == institution_id,
            )
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise NotFoundException("Dataset not found")
        return dataset


def dataset_used_by(usage_scope: str | None) -> list[str]:
    if not usage_scope:
        return []
    return USAGE_CONSUMERS.get(usage_scope, [])
