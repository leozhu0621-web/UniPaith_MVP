"""Spec 24 — Institution Data Upload.

Owns every dataset operation: presigned upload, validation, normalization,
versioning + rollback, replace/append/export, preview + histogram, and the
reusable column-mapping templates. The heavy parsing/validation/normalization
logic lives as pure module-level functions so it is unit-testable without a DB.

Brand/scope rules (Spec 24 §11/§13): usage scope is enforced — a ``marketing``
dataset never feeds matching — via :meth:`DatasetService.list_for_purpose`.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from difflib import get_close_matches
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.core.s3 import S3Client
from unipaith.models import (
    DatasetMappingTemplate,
    DatasetVersion,
    InstitutionDataset,
    Program,
)

# --- Per-type field contracts (server is the source of truth) ---------------

PLATFORM_FIELDS: dict[str, list[str]] = {
    "prospect_list": [
        "email",
        "first_name",
        "last_name",
        "phone",
        "nationality",
        "country",
        "degree_interest",
        "program_interest",
        "source",
        "notes",
    ],
    "admissions_history": [
        "student_email",
        "program_name",
        "application_date",
        "decision",
        "gpa",
        "test_score",
        "enrollment_status",
    ],
    "outcomes_summary": [
        "program_name",
        "graduation_year",
        "employment_status",
        "employer",
        "salary_range",
        "time_to_employment",
    ],
}

# Fields that must be present + non-empty for a row to be valid.
REQUIRED_FIELDS: dict[str, list[str]] = {
    "prospect_list": ["email"],
    "admissions_history": ["student_email", "program_name", "application_date", "decision"],
    "outcomes_summary": ["program_name", "graduation_year"],
}

# Composite primary key used for duplicate detection.
PRIMARY_KEY: dict[str, list[str]] = {
    "prospect_list": ["email"],
    "admissions_history": ["student_email", "program_name"],
    "outcomes_summary": ["program_name", "graduation_year"],
}

# True date fields (validated against common formats).
DATE_FIELDS: dict[str, list[str]] = {
    "prospect_list": [],
    "admissions_history": ["application_date"],
    "outcomes_summary": [],
}

# The platform field that names a program (drives normalization → programs.id).
PROGRAM_FIELD: dict[str, str | None] = {
    "prospect_list": None,
    "admissions_history": "program_name",
    "outcomes_summary": "program_name",
}

_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y")

# Spec 24 §15 — configurable max upload size; chunked streaming for >100MB
# deferred. 50MB covers the institution datasets we expect at MVP.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


# --- Pure helpers (no DB) ----------------------------------------------------


def parse_tabular(content: bytes, file_name: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Parse CSV / TSV / xlsx bytes into (columns, rows). Raises BadRequest on
    an unreadable or unsupported file."""
    name = (file_name or "").lower()
    try:
        if name.endswith((".xlsx", ".xlsm")):
            return _parse_xlsx(content)
        text = content.decode("utf-8-sig")
        delimiter = "\t" if name.endswith((".tsv", ".tab")) else ","
        if not name.endswith((".tsv", ".tab", ".csv")) and "\t" in text.split("\n", 1)[0]:
            delimiter = "\t"  # sniff tab-separated content with a generic name
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        columns = [c for c in (reader.fieldnames or []) if c is not None]
        rows = [
            {k: (v if v is not None else "") for k, v in r.items() if k is not None} for r in reader
        ]
        return columns, rows
    except BadRequestException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise BadRequestException(f"Could not parse file: {exc}") from exc


def _parse_xlsx(content: bytes) -> tuple[list[str], list[dict[str, Any]]]:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        header = next(rows_iter)
    except StopIteration:
        return [], []
    columns = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(header)]
    rows: list[dict[str, Any]] = []
    for raw in rows_iter:
        if raw is None or all(c is None for c in raw):
            continue
        row = {}
        for i, col in enumerate(columns):
            val = raw[i] if i < len(raw) else None
            row[col] = "" if val is None else str(val)
        rows.append(row)
    wb.close()
    return columns, rows


def apply_mapping(rows: list[dict], mapping: dict[str, str]) -> list[dict]:
    """Project uploaded rows onto platform fields using ``mapping`` (uploaded
    column → platform field). Unmapped/empty targets are skipped."""
    out = []
    for r in rows:
        mapped: dict[str, Any] = {}
        for src, target in (mapping or {}).items():
            if target:
                mapped[target] = r.get(src, "")
        out.append(mapped)
    return out


def _is_blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def parse_date(value: str) -> date | None:
    v = (value or "").strip()
    if not v:
        return None
    try:
        return datetime.fromisoformat(v).date()
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def validate_rows(
    dataset_type: str,
    mapped_rows: list[dict],
    valid_program_names: set[str] | None = None,
    program_suggestions: list[str] | None = None,
) -> dict[str, Any]:
    """Build the Spec 24 §7 validation report from mapped rows. Row indices are
    1-based to match what an institution sees in their spreadsheet."""
    required = REQUIRED_FIELDS.get(dataset_type, [])
    pk = PRIMARY_KEY.get(dataset_type, [])
    date_fields = DATE_FIELDS.get(dataset_type, [])
    program_field = PROGRAM_FIELD.get(dataset_type)

    missing_required: list[dict] = []
    duplicates: list[dict] = []
    invalid_dates: list[dict] = []
    unmappable_programs: list[dict] = []
    seen: dict[str, int] = {}

    for idx, row in enumerate(mapped_rows, start=1):
        missing = [f for f in required if _is_blank(row.get(f))]
        if missing:
            missing_required.append({"row": idx, "fields": missing})

        if pk and not any(_is_blank(row.get(k)) for k in pk):
            key = "|".join(str(row.get(k, "")).strip().lower() for k in pk)
            if key in seen:
                duplicates.append({"row": idx, "key": key, "first_seen_row": seen[key]})
            else:
                seen[key] = idx

        for f in date_fields:
            raw = row.get(f)
            if not _is_blank(raw) and parse_date(str(raw)) is None:
                invalid_dates.append({"row": idx, "field": f, "value": str(raw)})

        # graduation_year is a year, not a full date — light sanity check.
        if dataset_type == "outcomes_summary" and not _is_blank(row.get("graduation_year")):
            yr = str(row["graduation_year"]).strip()
            if not (yr.isdigit() and 1900 <= int(yr) <= 2100):
                invalid_dates.append({"row": idx, "field": "graduation_year", "value": yr})

        if program_field and valid_program_names is not None:
            val = str(row.get(program_field, "")).strip()
            if val and val.lower() not in valid_program_names:
                sugg = get_close_matches(val, program_suggestions or [], n=3, cutoff=0.4)
                unmappable_programs.append({"row": idx, "value": val, "suggestions": sugg})

    bad_rows = {e["row"] for e in missing_required} | {e["row"] for e in duplicates}
    bad_rows |= {e["row"] for e in invalid_dates} | {e["row"] for e in unmappable_programs}
    total = len(mapped_rows)
    valid = total - len(bad_rows)

    issue_bits = []
    if missing_required:
        issue_bits.append(f"{len(missing_required)} with missing fields")
    if duplicates:
        issue_bits.append(f"{len(duplicates)} duplicates")
    if invalid_dates:
        issue_bits.append(f"{len(invalid_dates)} invalid dates")
    if unmappable_programs:
        issue_bits.append(f"{len(unmappable_programs)} unmappable programs")
    summary = f"{valid} of {total} rows valid" + (
        f"; {', '.join(issue_bits)}." if issue_bits else "; no issues found."
    )

    return {
        "total_rows": total,
        "valid_rows": valid,
        "missing_required": missing_required,
        "duplicates": duplicates,
        "invalid_dates": invalid_dates,
        "unmappable_programs": unmappable_programs,
        "summary": summary,
        "source": "rule_based",
    }


def build_histogram(columns: list[str], rows: list[dict], top_n: int = 6) -> dict[str, Any]:
    """Per-column value distribution: top values + null count + distinct count.
    Bounded by ``rows`` already sliced by the caller (preview is 100 rows)."""
    hist: dict[str, Any] = {}
    for col in columns:
        counts: dict[str, int] = {}
        nulls = 0
        for r in rows:
            v = r.get(col)
            if _is_blank(v):
                nulls += 1
                continue
            key = str(v).strip()
            counts[key] = counts.get(key, 0) + 1
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
        hist[col] = {
            "top": [{"value": k, "count": c} for k, c in top],
            "null_count": nulls,
            "distinct": len(counts),
        }
    return hist


def _row_keys(dataset_type: str, mapped_rows: list[dict]) -> set[str]:
    pk = PRIMARY_KEY.get(dataset_type, [])
    keys = set()
    for row in mapped_rows:
        if pk and not any(_is_blank(row.get(k)) for k in pk):
            keys.add("|".join(str(row.get(k, "")).strip().lower() for k in pk))
    return keys


# --- Service -----------------------------------------------------------------


class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3 = S3Client()

    # -- ownership --
    async def _verify_ownership(self, institution_id: UUID, dataset_id: UUID) -> InstitutionDataset:
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

    # -- S3 read/write (local-mode aware) --
    def _read_bytes(self, s3_key: str) -> bytes | None:
        if settings.s3_local_mode:
            p = Path(settings.s3_local_path) / s3_key
            return p.read_bytes() if p.exists() else None
        import boto3

        client = boto3.client("s3", region_name=settings.aws_region)
        try:
            obj = client.get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
            return obj["Body"].read()
        except Exception:
            return None

    def _write_bytes(self, s3_key: str, content: bytes) -> None:
        if settings.s3_local_mode:
            p = Path(settings.s3_local_path) / s3_key
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content)
            return
        import boto3

        client = boto3.client("s3", region_name=settings.aws_region)
        client.put_object(Bucket=settings.s3_bucket_name, Key=s3_key, Body=content)

    # -- programs (for normalization) --
    async def _programs(self, institution_id: UUID) -> list[Program]:
        result = await self.db.execute(
            select(Program).where(Program.institution_id == institution_id)
        )
        return list(result.scalars().all())

    async def _program_lookup(
        self, institution_id: UUID
    ) -> tuple[set[str], list[str], dict[str, str]]:
        programs = await self._programs(institution_id)
        names_lower = {p.program_name.strip().lower() for p in programs}
        names = [p.program_name for p in programs]
        name_to_id = {p.program_name.strip().lower(): str(p.id) for p in programs}
        return names_lower, names, name_to_id

    # -- list / read --
    async def list_datasets(
        self, institution_id: UUID, type_filter: str | None = None
    ) -> list[InstitutionDataset]:
        stmt = select(InstitutionDataset).where(InstitutionDataset.institution_id == institution_id)
        if type_filter and type_filter != "all":
            stmt = stmt.where(InstitutionDataset.dataset_type == type_filter)
        stmt = stmt.order_by(InstitutionDataset.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_for_purpose(
        self, institution_id: UUID, purpose: str
    ) -> list[InstitutionDataset]:
        """Spec 24 §13 — usage-scope enforcement. ``purpose`` ∈
        {matching, marketing, analytics}. A dataset feeds a purpose only if its
        scope is ``all`` or matches; ``matching`` maps to the ``admissions`` scope.
        A ``marketing``-scope dataset is therefore never returned for matching."""
        scope_for = {
            "matching": "admissions",
            "admissions": "admissions",
            "marketing": "marketing",
            "analytics": "analytics",
        }
        needed = scope_for.get(purpose, purpose)
        datasets = await self.list_datasets(institution_id)
        return [d for d in datasets if d.usage_scope in (needed, "all")]

    @staticmethod
    def scope_allows(dataset: InstitutionDataset, purpose: str) -> bool:
        scope_for = {
            "matching": "admissions",
            "admissions": "admissions",
            "marketing": "marketing",
            "analytics": "analytics",
        }
        needed = scope_for.get(purpose, purpose)
        return dataset.usage_scope in (needed, "all")

    async def get_dataset_with_url(
        self, institution_id: UUID, dataset_id: UUID
    ) -> InstitutionDataset:
        return await self._verify_ownership(institution_id, dataset_id)

    def download_url(self, dataset: InstitutionDataset) -> str:
        return self.s3.generate_download_url(dataset.s3_key)

    # -- upload (spec §8: upload-url + confirm-upload) --
    def request_upload_url(self, institution_id: UUID, file_name: str, content_type: str) -> dict:
        file_ref = f"datasets/{institution_id}/{uuid4()}/{file_name}"
        upload_url = self.s3.generate_upload_url(file_ref, content_type)
        return {"file_ref": file_ref, "upload_url": upload_url}

    def store_upload(self, institution_id: UUID, file_name: str, content: bytes) -> dict:
        """Direct upload — writes the file to storage and returns its ref. Used
        by the multipart upload endpoint (reliable across local + prod; avoids
        browser→S3 CORS). ``request_upload_url`` remains for presigned large
        files (Spec 24 §8 / §15)."""
        if len(content) > MAX_UPLOAD_BYTES:
            raise BadRequestException(
                f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit."
            )
        file_ref = f"datasets/{institution_id}/{uuid4()}/{file_name}"
        self._write_bytes(file_ref, content)
        return {"file_ref": file_ref, "file_name": file_name, "size_bytes": len(content)}

    async def inspect(self, file_ref: str) -> dict:
        """Return detected columns + sample rows + histogram for the mapping
        step, without creating a dataset."""
        content = self._read_bytes(file_ref)
        if content is None:
            raise BadRequestException("Uploaded file not found. Re-upload and try again.")
        if len(content) > MAX_UPLOAD_BYTES:
            raise BadRequestException(
                f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit."
            )
        columns, rows = parse_tabular(content, file_ref)
        sample = rows[:100]
        return {
            "columns": columns,
            "rows": sample,
            "total_rows": len(rows),
            "histogram": build_histogram(columns, sample),
        }

    async def validate_dry_run(
        self,
        institution_id: UUID,
        dataset_type: str,
        mapping: dict[str, str],
        file_ref: str,
    ) -> dict:
        """Dry-run validation + normalization suggestions for the wizard."""
        content = self._read_bytes(file_ref)
        if content is None:
            raise BadRequestException("Uploaded file not found. Re-upload and try again.")
        _columns, rows = parse_tabular(content, file_ref)
        mapped = apply_mapping(rows, mapping)
        names_lower, names, name_to_id = await self._program_lookup(institution_id)
        report = validate_rows(dataset_type, mapped, names_lower, names)
        normalization_map = self._build_normalization_map(dataset_type, mapped, name_to_id)
        return {"validation_report": report, "normalization_map": normalization_map}

    def _build_normalization_map(
        self, dataset_type: str, mapped_rows: list[dict], name_to_id: dict[str, str]
    ) -> dict[str, str]:
        field = PROGRAM_FIELD.get(dataset_type)
        if not field:
            return {}
        out: dict[str, str] = {}
        for row in mapped_rows:
            val = str(row.get(field, "")).strip()
            if val and val.lower() in name_to_id:
                out[val] = name_to_id[val.lower()]
        return out

    async def confirm_upload(
        self,
        institution_id: UUID,
        user_id: UUID,
        *,
        name: str,
        dataset_type: str,
        file_ref: str,
        file_name: str,
        mapping: dict[str, str],
        description: str | None = None,
        usage_scope: str | None = None,
        coverage_start: date | None = None,
        coverage_end: date | None = None,
        file_size_bytes: int | None = None,
    ) -> InstitutionDataset:
        content = self._read_bytes(file_ref)
        if content is None:
            raise BadRequestException("Uploaded file not found. Re-upload and try again.")
        if len(content) > MAX_UPLOAD_BYTES:
            raise BadRequestException(
                f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit."
            )

        _columns, rows = parse_tabular(content, file_name)
        mapped = apply_mapping(rows, mapping)
        names_lower, names, name_to_id = await self._program_lookup(institution_id)
        report = validate_rows(dataset_type, mapped, names_lower, names)
        report = await self._maybe_triage(content, file_name, dataset_type, report)
        normalization_map = self._build_normalization_map(dataset_type, mapped, name_to_id)

        dataset = InstitutionDataset(
            institution_id=institution_id,
            dataset_name=name,
            dataset_type=dataset_type,
            description=description,
            s3_key=file_ref,
            file_name=file_name,
            file_size_bytes=file_size_bytes if file_size_bytes is not None else len(content),
            row_count=len(rows),
            column_mapping=mapping,
            normalization_map=normalization_map,
            validation_errors=report,
            usage_scope=usage_scope,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            status="validated" if report["valid_rows"] == report["total_rows"] else "processed",
            version=1,
            uploaded_by=user_id,
        )
        self.db.add(dataset)
        await self.db.flush()

        await self._add_version(
            dataset,
            user_id,
            s3_key=file_ref,
            row_count=len(rows),
            changes_summary={
                "added": len(rows),
                "modified": 0,
                "invalidated": _invalid_count(report),
            },
            validation_report=report,
        )
        await self.db.refresh(dataset)
        return dataset

    async def _add_version(
        self,
        dataset: InstitutionDataset,
        user_id: UUID | None,
        *,
        s3_key: str,
        row_count: int | None,
        changes_summary: dict,
        validation_report: dict | None,
        version_number: int | None = None,
    ) -> DatasetVersion:
        if version_number is None:
            version_number = dataset.version
        version = DatasetVersion(
            dataset_id=dataset.id,
            version_number=version_number,
            s3_key=s3_key,
            row_count=row_count,
            changes_summary=changes_summary,
            validation_report=validation_report,
            uploaded_by=user_id,
        )
        self.db.add(version)
        await self.db.flush()
        return version

    # -- preview / validation --
    async def get_preview(self, institution_id: UUID, dataset_id: UUID, limit: int = 100) -> dict:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        content = self._read_bytes(dataset.s3_key)
        if content is None:
            return {"columns": [], "rows": [], "total_rows": 0, "histogram": {}}
        columns, rows = parse_tabular(content, dataset.file_name)
        sample = rows[:limit]
        if dataset.row_count is None:
            dataset.row_count = len(rows)
            await self.db.flush()
        return {
            "columns": columns,
            "rows": sample,
            "total_rows": len(rows),
            "histogram": build_histogram(columns, sample),
        }

    async def get_validation(self, institution_id: UUID, dataset_id: UUID) -> dict:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        if dataset.validation_errors:
            return dataset.validation_errors
        # recompute from current file
        content = self._read_bytes(dataset.s3_key)
        if content is None:
            return validate_rows(dataset.dataset_type, [])
        _columns, rows = parse_tabular(content, dataset.file_name)
        mapped = apply_mapping(rows, dataset.column_mapping or {})
        names_lower, names, _ = await self._program_lookup(institution_id)
        return validate_rows(dataset.dataset_type, mapped, names_lower, names)

    # -- mutate --
    async def update_dataset(
        self, institution_id: UUID, dataset_id: UUID, data: dict
    ) -> InstitutionDataset:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        for key, value in data.items():
            if value is not None and hasattr(dataset, key):
                setattr(dataset, key, value)
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset

    async def delete_dataset(self, institution_id: UUID, user_id: UUID, dataset_id: UUID) -> dict:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        snapshot = {
            "dataset_name": dataset.dataset_name,
            "dataset_type": dataset.dataset_type,
            "row_count": dataset.row_count,
        }
        # delete all version snapshots from storage (+ the head file). Query the
        # version keys explicitly — accessing dataset.versions would trigger an
        # async lazy-load. The DB row cascade handles the version rows.
        result = await self.db.execute(
            select(DatasetVersion.s3_key).where(DatasetVersion.dataset_id == dataset_id)
        )
        keys = {dataset.s3_key} | {row[0] for row in result.all()}
        for key in keys:
            try:
                self.s3.delete_object(key)
            except Exception:
                pass
        await self.db.delete(dataset)
        await self.db.flush()
        return snapshot

    async def replace_dataset(
        self,
        institution_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        file_ref: str,
        file_name: str,
        mapping: dict | None = None,
    ) -> InstitutionDataset:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        content = self._read_bytes(file_ref)
        if content is None:
            raise BadRequestException("Uploaded file not found. Re-upload and try again.")
        new_map = mapping or dataset.column_mapping or {}
        _columns, new_rows = parse_tabular(content, file_name)
        mapped = apply_mapping(new_rows, new_map)

        # diff vs current head file for the changes summary
        old_content = self._read_bytes(dataset.s3_key)
        old_keys = set()
        if old_content is not None:
            _oc, old_rows = parse_tabular(old_content, dataset.file_name)
            old_keys = _row_keys(
                dataset.dataset_type, apply_mapping(old_rows, dataset.column_mapping or {})
            )
        new_keys = _row_keys(dataset.dataset_type, mapped)
        added = len(new_keys - old_keys)
        invalidated = len(old_keys - new_keys)
        modified = len(new_keys & old_keys)

        names_lower, names, name_to_id = await self._program_lookup(institution_id)
        report = validate_rows(dataset.dataset_type, mapped, names_lower, names)
        report = await self._maybe_triage(content, file_name, dataset.dataset_type, report)

        dataset.s3_key = file_ref
        dataset.file_name = file_name
        dataset.column_mapping = new_map
        dataset.normalization_map = self._build_normalization_map(
            dataset.dataset_type, mapped, name_to_id
        )
        dataset.row_count = len(new_rows)
        dataset.validation_errors = report
        dataset.file_size_bytes = len(content)
        dataset.version += 1
        dataset.status = (
            "validated" if report["valid_rows"] == report["total_rows"] else "processed"
        )
        await self.db.flush()
        await self._add_version(
            dataset,
            user_id,
            s3_key=file_ref,
            row_count=len(new_rows),
            changes_summary={"added": added, "modified": modified, "invalidated": invalidated},
            validation_report=report,
        )
        await self.db.refresh(dataset)
        return dataset

    async def append_dataset(
        self,
        institution_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        file_ref: str,
        file_name: str,
    ) -> InstitutionDataset:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        add_content = self._read_bytes(file_ref)
        if add_content is None:
            raise BadRequestException("Uploaded file not found. Re-upload and try again.")
        cur_content = self._read_bytes(dataset.s3_key)
        cur_cols, cur_rows = (
            parse_tabular(cur_content, dataset.file_name) if cur_content else ([], [])
        )
        add_cols, add_rows = parse_tabular(add_content, file_name)
        columns = cur_cols or add_cols
        combined = cur_rows + [{c: r.get(c, "") for c in columns} for r in add_rows]

        # write the concatenated file to a fresh key (preserve prior version file)
        new_key = f"datasets/{institution_id}/{uuid4()}/{dataset.file_name}"
        self._write_bytes(new_key, _rows_to_csv(columns, combined).encode("utf-8"))

        mapped = apply_mapping(combined, dataset.column_mapping or {})
        names_lower, names, name_to_id = await self._program_lookup(institution_id)
        report = validate_rows(dataset.dataset_type, mapped, names_lower, names)

        dataset.s3_key = new_key
        dataset.row_count = len(combined)
        dataset.normalization_map = self._build_normalization_map(
            dataset.dataset_type, mapped, name_to_id
        )
        dataset.validation_errors = report
        dataset.version += 1
        dataset.status = (
            "validated" if report["valid_rows"] == report["total_rows"] else "processed"
        )
        await self.db.flush()
        await self._add_version(
            dataset,
            user_id,
            s3_key=new_key,
            row_count=len(combined),
            changes_summary={"added": len(add_rows), "modified": 0, "invalidated": 0},
            validation_report=report,
        )
        await self.db.refresh(dataset)
        return dataset

    async def export_csv(self, institution_id: UUID, dataset_id: UUID) -> tuple[str, str]:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        content = self._read_bytes(dataset.s3_key)
        if content is None:
            return "", dataset.file_name
        columns, rows = parse_tabular(content, dataset.file_name)
        return _rows_to_csv(columns, rows), dataset.file_name

    # -- versions --
    async def list_versions(self, institution_id: UUID, dataset_id: UUID) -> list[DatasetVersion]:
        await self._verify_ownership(institution_id, dataset_id)
        result = await self.db.execute(
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def rollback(
        self, institution_id: UUID, user_id: UUID, dataset_id: UUID, version_number: int
    ) -> InstitutionDataset:
        dataset = await self._verify_ownership(institution_id, dataset_id)
        result = await self.db.execute(
            select(DatasetVersion).where(
                DatasetVersion.dataset_id == dataset_id,
                DatasetVersion.version_number == version_number,
            )
        )
        target = result.scalar_one_or_none()
        if not target:
            raise NotFoundException("Version not found")
        content = self._read_bytes(target.s3_key)
        row_count = target.row_count
        if content is not None:
            _columns, rows = parse_tabular(content, dataset.file_name)
            row_count = len(rows)
        dataset.s3_key = target.s3_key
        dataset.row_count = row_count
        dataset.validation_errors = target.validation_report
        dataset.version += 1
        dataset.status = "processed"
        await self.db.flush()
        await self._add_version(
            dataset,
            user_id,
            s3_key=target.s3_key,
            row_count=row_count,
            changes_summary={
                "added": 0,
                "modified": 0,
                "invalidated": 0,
                "note": f"Rolled back to v{version_number}",
            },
            validation_report=target.validation_report,
        )
        await self.db.refresh(dataset)
        return dataset

    # -- mapping templates --
    async def list_templates(
        self, institution_id: UUID, dataset_type: str | None = None
    ) -> list[DatasetMappingTemplate]:
        stmt = select(DatasetMappingTemplate).where(
            DatasetMappingTemplate.institution_id == institution_id
        )
        if dataset_type:
            stmt = stmt.where(DatasetMappingTemplate.dataset_type == dataset_type)
        stmt = stmt.order_by(DatasetMappingTemplate.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_template(
        self,
        institution_id: UUID,
        user_id: UUID,
        *,
        name: str,
        dataset_type: str,
        column_mapping: dict,
    ) -> DatasetMappingTemplate:
        # upsert by (institution, type, name)
        result = await self.db.execute(
            select(DatasetMappingTemplate).where(
                DatasetMappingTemplate.institution_id == institution_id,
                DatasetMappingTemplate.dataset_type == dataset_type,
                DatasetMappingTemplate.name == name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.column_mapping = column_mapping
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        tpl = DatasetMappingTemplate(
            institution_id=institution_id,
            dataset_type=dataset_type,
            name=name,
            column_mapping=column_mapping,
            created_by=user_id,
        )
        self.db.add(tpl)
        await self.db.flush()
        await self.db.refresh(tpl)
        return tpl

    async def delete_template(self, institution_id: UUID, template_id: UUID) -> None:
        result = await self.db.execute(
            select(DatasetMappingTemplate).where(
                DatasetMappingTemplate.id == template_id,
                DatasetMappingTemplate.institution_id == institution_id,
            )
        )
        tpl = result.scalar_one_or_none()
        if not tpl:
            raise NotFoundException("Template not found")
        await self.db.delete(tpl)
        await self.db.flush()

    # -- AI triage (Spec 24 §9 / 45 §19) --
    async def _maybe_triage(
        self, content: bytes, file_name: str, dataset_type: str, report: dict
    ) -> dict:
        """Enrich the deterministic report with a DocumentParseTriage summary.
        On any failure the rule-based report is returned unchanged (Plan-2
        integration-test invariant — never raise to the caller)."""
        if not settings.ai_data_parse_triage_v2_enabled:
            return report
        try:
            from unipaith.ai.document_parse_triage import triage_parse

            triaged = await triage_parse(
                file_name=file_name,
                dataset_type=dataset_type,
                size_bytes=len(content),
                report=report,
            )
            if triaged:
                report = {**report, **triaged, "source": "ai"}
        except Exception:
            return report
        return report


def _invalid_count(report: dict) -> int:
    return (
        len(report.get("missing_required", []))
        + len(report.get("invalid_dates", []))
        + len(report.get("unmappable_programs", []))
    )


def _rows_to_csv(columns: list[str], rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({c: r.get(c, "") for c in columns})
    return buf.getvalue()
