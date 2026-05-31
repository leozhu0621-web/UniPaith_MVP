# 24 · Data Upload — Institution Datasets

> The workspace institutions use to upload their own datasets (admissions history, prospect lists, outcomes summaries) so the platform can use them for segmentation, campaigns, analytics, and workflow setup.
>
> Status: **draft v1.0** · 2026-05-29 · Route: `/i/data`.

---

## 1. Purpose

Institutions have data the platform doesn't generate itself. The Data Upload workspace lets them:
- Bring in historical admissions data for matching-model training (per consent).
- Bring in prospect lists for outreach campaigns.
- Bring in outcomes data for the program's Outcomes tab.

Each dataset has scope, versioning, and validation.

---

## 2. Workspace structure

```
DATA
Your datasets

[Filter: All ▾]  [+ Upload dataset]

┌─────────────────────────────────────────────────────────────────────┐
│ Admissions History 2020-2024                                         │
│ Type: admissions_history · 12,450 rows                               │
│ Updated: 2 days ago · Used by: matching                              │
│ [Preview] [Edit] [Replace] [Delete]                                  │
└─────────────────────────────────────────────────────────────────────┘
... rows
```

---

## 3. Dataset types

| Type | Purpose | Notes |
|---|---|---|
| `admissions_history` | Historical applicant/decision data for matching-model training (consent-gated). | High-PII; encrypted at rest. |
| `prospect_list` | CSV contacts for outreach (Campaigns external email). | PII; opt-in expected by sender. |
| `outcomes_summary` | Placement/salary aggregates for the Program Outcomes tab. | Low PII; aggregate-only. |

---

## 4. Upload flow

1. Click [+ Upload dataset].
2. Modal: name, type, optional description, coverage/time range.
3. Choose update method: **replace** dataset vs **append** new records.
4. File upload (CSV / TSV / xlsx).
5. **Column mapping** — map uploaded columns to platform standard fields. Save mapping as a template for reuse.
6. **Normalization** — institution's program identifiers mapped to UniPaith's program records.
7. **Validation** — missing fields, duplicates, invalid dates, basic consistency. Upload error report generated.
8. **Set dataset usage scope** — marketing only / admissions ops only / analytics only / all.
9. Submit → dataset created.

---

## 5. Per-dataset actions

- **Preview** — first 100 rows + column histogram.
- **Edit** — name, description, usage scope.
- **Replace** — re-upload with same mapping.
- **Append** — add new rows.
- **Delete** — confirmation modal; audit-logged.
- **Export** — back to CSV.

---

## 6. Versioning

Every dataset write creates a version. The institution can:
- View change summaries per version ("250 rows added; 30 modified; 5 invalidated").
- Roll back to a prior version.

---

## 7. Validation report

After upload, surfaces:
- Rows with missing required fields → row indices.
- Duplicate rows by primary key → row indices.
- Invalid dates → row indices + value seen.
- Unmappable program identifiers → row indices + suggested matches.

Institution can correct or skip and retry.

---

## 8. Data shape

```ts
type Dataset = {
  id: string;
  institution_id: string;
  name: string;
  type: 'admissions_history' | 'prospect_list' | 'outcomes_summary';
  description: string;
  coverage_start: date | null;
  coverage_end: date | null;
  row_count: number;
  usage_scope: 'marketing' | 'admissions' | 'analytics' | 'all';
  column_mapping: Record<string, string>;     // uploaded column → platform field
  versions: DatasetVersion[];
  uploaded_by: UserRef;
  created_at: ISO8601;
  updated_at: ISO8601;
};

type DatasetVersion = {
  id: string;
  dataset_id: string;
  version_number: number;
  uploaded_at: ISO8601;
  changes_summary: { added: number; modified: number; invalidated: number };
  validation_report: ValidationReport;
};
```

Endpoints:
- `GET /i/datasets`.
- `POST /i/datasets/upload-url` — pre-signed S3 URL.
- `POST /i/datasets/confirm-upload` — body: `{name, type, mapping, scope, file_ref}`.
- `GET /i/datasets/:id/preview?limit=100`.
- `PATCH /i/datasets/:id`.
- `DELETE /i/datasets/:id`.
- `POST /i/datasets/:id/replace` / `append`.
- `GET /i/datasets/:id/versions`.

---

## 9. AI integration

| Agent | Trigger | Purpose |
|---|---|---|
| `DocumentParseTriage` (`45` §19) | On upload | Triage parse success/failure |
| (Future) `MappingSuggester` | On column mapping step | Suggest column → field mappings |

---

## 10. States

- **Empty:** "Upload a dataset to power matching, campaigns, or analytics."
- **Upload in progress:** progress bar.
- **Validation errors:** modal lists issues + "Skip invalid rows / Cancel" CTAs.

---

## 11. Brand compliance

- Tables per `02` §8.
- Status badges (uploaded / validated / processed / failed) using semantic status colors.
- No gold in this workspace (operational, not celebratory).

---

## 12. Gaps (from `47`)

- Bulk-import column-mapping persistence: spec calls for mapping templates saved for reuse; current implementation saves per-upload.

---

## 13. Tests

- Upload → validate → confirm flow.
- Mapping templates reusable across uploads.
- Versioning + rollback.
- Usage scope enforcement (a `marketing`-scope dataset never feeds matching).

---

## 14. Copy

- "Upload a dataset to power matching, campaigns, or analytics."
- "Map your columns to platform fields" (mapping step header).
- "Skip invalid rows" / "Cancel".
- "Replace this dataset?" (confirm modal).

---

## 15. Open questions

- **Streaming uploads for large files.** > 100MB CSVs require chunked S3 + server-side streaming parse. Current limit?
- **PII redaction at ingest.** When a `prospect_list` is uploaded, should we strip phone numbers for students who opted out? Yes, post-ingest match against the platform's opt-out list.
- **Dataset → consent alignment.** Datasets used for matching require students whose data is in them to have `consent.matching=true` at the time of model use. Cross-check job needed.
