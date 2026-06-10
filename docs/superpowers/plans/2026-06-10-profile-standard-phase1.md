# Profile Standard — Phase 1 (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make MIT/Sloan/MBAn the machine-checkable canonical standard for the three profile levels — a versioned manifest + sourcing playbook + a conformance checker that certifies the MIT trio and detects every gap on any other profile.

**Architecture:** A new net-additive backend package `profile_standard/` holds a versioned manifest (sections → fields → JSONB path → sourcing rule, extracted only from MIT/Sloan/MBAn) and a pure conformance function. No data migration, no refactor of the existing profile modules in this phase — Phase 1 only *defines and checks* the standard. The shared-base refactor and enrichment engine come in later phases.

**Tech Stack:** Python 3.12, dataclasses, pytest. Frontend parity test in vitest (reads a generated `manifest.json`).

---

## File Structure

- `unipaith-backend/src/unipaith/profile_standard/__init__.py` — exports `STANDARD_VERSION`, `MANIFEST`, `check_conformance`.
- `unipaith-backend/src/unipaith/profile_standard/manifest.py` — `STANDARD_VERSION`, `Field`/`Section` dataclasses, `MANIFEST: dict[level -> list[Section]]`.
- `unipaith-backend/src/unipaith/profile_standard/conformance.py` — `check_conformance(level, snapshot) -> ConformanceResult`.
- `unipaith-backend/src/unipaith/profile_standard/playbook.md` — per-field sourcing/wording rules.
- `unipaith-backend/src/unipaith/profile_standard/export_manifest.py` — writes `frontend/src/generated/profile-manifest.json`.
- `unipaith-backend/tests/test_profile_standard.py` — conformance unit tests + MIT-trio certification.
- `frontend/src/generated/profile-manifest.json` — generated artifact (committed).
- `frontend/src/test/profile-manifest-parity.test.ts` — every manifest section id appears in the matching detail page.

---

### Task 1: Manifest dataclasses + version + the three-level field map

**Files:**
- Create: `unipaith-backend/src/unipaith/profile_standard/manifest.py`

- [ ] **Step 1: Write `manifest.py`** — `STANDARD_VERSION = 1`, the dataclasses, and the field map grounded in the real MIT trio keys.

```python
"""The canonical profile standard — extracted ONLY from the MIT / Sloan / MBAn
reference instance. Bumping STANDARD_VERSION re-conforms the whole fleet."""
from __future__ import annotations

from dataclasses import dataclass, field

STANDARD_VERSION = 1

# Sourcing rule references resolved by the playbook (and Phase-2 verification gate).
SOURCING = {
    "first_party": "One designated first-party/official source; citation required.",
    "authoritative_2x": "Two independent authoritative sources must agree; citation required.",
    "official_or_curated": "Official page or curated editorial; citation when a stat.",
    "none": "Structural/derived; no external citation required.",
}


@dataclass(frozen=True)
class Field:
    key: str            # leaf name
    label: str          # human label
    path: str           # dotted location in the level snapshot, e.g. "outcomes_data.median_salary"
    required: bool = True
    sourcing: str = "official_or_curated"
    cited: bool = False  # if True, the field's container must carry source/source_url


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    order: int
    fields: list[Field]
    required: bool = True
    widget: str = "stat-grid"


# --- Institution level (renders InstitutionDetail) ---
INSTITUTION: list[Section] = [
    Section("identity", "Identity & description", 1, widget="prose", fields=[
        Field("description_text", "Description", "description_text", sourcing="official_or_curated"),
        Field("student_body_size", "Student body size", "student_body_size", sourcing="first_party"),
        Field("campus_photo", "Campus photo", "media_gallery", sourcing="none"),
    ]),
    Section("rankings", "Rankings & classification", 2, widget="chip-list", fields=[
        Field("qs_world_university_rankings", "QS world rank", "ranking_data.qs_world_university_rankings", sourcing="first_party"),
        Field("times_higher_education", "THE rank", "ranking_data.times_higher_education", sourcing="first_party"),
        Field("us_news_national", "US News national", "ranking_data.us_news_national", sourcing="first_party"),
        Field("carnegie_classification", "Carnegie classification", "ranking_data.carnegie_classification", sourcing="first_party"),
        Field("accreditor", "Accreditor", "ranking_data.accreditor", sourcing="first_party"),
    ]),
    Section("report_card", "Report-card key stats", 3, fields=[
        Field("admit_rate", "Admit rate", "school_outcomes.admit_rate", sourcing="first_party"),
        Field("avg_net_price", "Average net price", "school_outcomes.avg_net_price", sourcing="first_party"),
        Field("median_earnings_10yr", "Median earnings (10yr)", "school_outcomes.median_earnings_10yr", sourcing="authoritative_2x"),
        Field("graduation_rate_6yr", "6-yr graduation rate", "school_outcomes.graduation_rate_6yr", sourcing="first_party"),
        Field("retention_rate_first_year", "First-year retention", "school_outcomes.retention_rate_first_year", sourcing="first_party"),
    ]),
    Section("admissions_funnel", "Admissions funnel", 4, fields=[
        Field("test_scores", "Test scores", "school_outcomes.test_scores", sourcing="first_party"),
        Field("demographics", "Demographics", "school_outcomes.demographics", required=False, sourcing="first_party"),
    ]),
    Section("campus_resources", "Campus resources", 5, widget="chip-list", fields=[
        Field("research", "Research & labs", "school_outcomes.research", sourcing="official_or_curated"),
        Field("campus_life", "Campus life", "school_outcomes.campus_life", sourcing="official_or_curated"),
    ]),
    Section("feeds", "Events & updates feeds", 6, widget="none", required=False, fields=[
        Field("content_sources", "Channel feeds + socials", "content_sources", sourcing="first_party"),
    ]),
    Section("citation", "Sources", 7, widget="citation-block", fields=[
        Field("sources", "Source citations", "school_outcomes.sources", sourcing="none", cited=False),
    ]),
]

# --- School level (renders SchoolSubunitPage) ---
SCHOOL: list[Section] = [
    Section("identity", "Identity", 1, widget="prose", fields=[
        Field("name", "Name", "name", sourcing="first_party"),
        Field("description", "Description", "description", sourcing="official_or_curated"),
        Field("website_url", "Website", "website_url", sourcing="first_party"),
    ]),
    Section("about_detail", "About — facts, leadership, faculty", 2, fields=[
        Field("founded", "Founded", "about_detail.founded", sourcing="first_party"),
        Field("leadership", "Leadership", "about_detail.leadership", sourcing="first_party"),
        Field("faculty", "Notable faculty", "about_detail.faculty", sourcing="official_or_curated"),
        Field("research_centers", "Research centers", "about_detail.research_centers", sourcing="official_or_curated"),
        Field("source", "Source", "about_detail.source", required=False, sourcing="none"),
    ]),
    Section("feeds", "Events & updates feeds", 3, widget="none", required=False, fields=[
        Field("content_sources", "Channel feeds + socials", "content_sources", sourcing="first_party"),
    ]),
]

# --- Program level (renders ProgramDetailPage) ---
PROGRAM: list[Section] = [
    Section("basics", "Basic info", 1, fields=[
        Field("program_name", "Full program name", "program_name", sourcing="first_party"),
        Field("degree_type", "Degree", "degree_type", sourcing="first_party"),
        Field("duration_months", "Length", "duration_months", sourcing="first_party"),
        Field("delivery_format", "Format", "delivery_format", sourcing="first_party"),
        Field("description_text", "Description", "description_text", sourcing="official_or_curated"),
        Field("website_url", "Website", "website_url", sourcing="first_party"),
    ]),
    Section("admissions", "Admissions", 2, fields=[
        Field("materials", "Required materials", "application_requirements.materials", sourcing="first_party"),
        Field("deadlines", "Deadlines / timeline", "application_requirements.deadlines", sourcing="first_party"),
        Field("evaluation", "Evaluation criteria", "application_requirements.evaluation", required=False, sourcing="official_or_curated"),
        Field("req_source", "Requirements source", "application_requirements.source", sourcing="none"),
    ]),
    Section("costs", "Costs & aid", 3, fields=[
        Field("tuition_usd", "Tuition", "cost_data.tuition_usd", sourcing="first_party"),
        Field("total_cost_of_attendance", "Total cost of attendance", "cost_data.total_cost_of_attendance", required=False, sourcing="first_party"),
        Field("cost_source", "Cost source", "cost_data.source", sourcing="none"),
    ]),
    Section("outcomes", "Outcomes", 4, widget="distribution", fields=[
        Field("employment_rate", "Employment rate", "outcomes_data.employment_rate", sourcing="first_party"),
        Field("median_salary", "Median base salary", "outcomes_data.median_salary", sourcing="first_party"),
        Field("salary_25th", "25th percentile", "outcomes_data.salary_25th", required=False, sourcing="first_party"),
        Field("salary_75th", "75th percentile", "outcomes_data.salary_75th", required=False, sourcing="first_party"),
        Field("top_industries", "Top industries", "outcomes_data.top_industries", sourcing="first_party"),
        Field("conditions", "Methodology / conditions", "outcomes_data.conditions", sourcing="first_party"),
        Field("outcomes_source", "Outcomes source", "outcomes_data.source", sourcing="none"),
    ]),
    Section("insights", "Insights — class profile, faculty, reviews", 5, required=False, fields=[
        Field("class_profile", "Class profile", "class_profile.cohort_size", required=False, sourcing="first_party"),
        Field("faculty", "Faculty", "faculty.lead", required=False, sourcing="official_or_curated"),
        Field("reviews", "Reviews", "reviews.summary", required=False, sourcing="authoritative_2x"),
    ]),
]

MANIFEST: dict[str, list[Section]] = {
    "institution": INSTITUTION,
    "school": SCHOOL,
    "program": PROGRAM,
}
```

- [ ] **Step 2: Sanity check it imports.** Run: `cd unipaith-backend && PYTHONPATH=src .venv/bin/python -c "from unipaith.profile_standard import manifest as m; print(m.STANDARD_VERSION, len(m.MANIFEST))"` Expected: `1 3`.

- [ ] **Step 3: Commit.** `git add unipaith-backend/src/unipaith/profile_standard/manifest.py && git commit -m "feat(profile-standard): versioned manifest from MIT/Sloan/MBAn"`

---

### Task 2: Conformance checker

**Files:**
- Create: `unipaith-backend/src/unipaith/profile_standard/conformance.py`
- Create: `unipaith-backend/src/unipaith/profile_standard/__init__.py`

- [ ] **Step 1: Write the failing test** in `tests/test_profile_standard.py`:

```python
import pytest
from unipaith.profile_standard import check_conformance, STANDARD_VERSION

def test_empty_program_is_non_conformant():
    res = check_conformance("program", {})
    assert res.conformant is False
    assert "basics" in {m.split(".")[0] for m in res.missing_fields}
```

- [ ] **Step 2: Run it, expect ImportError/fail.** Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py::test_empty_program_is_non_conformant -q`

- [ ] **Step 3: Implement `conformance.py`:**

```python
"""Pure conformance check: does a profile snapshot satisfy the manifest?"""
from __future__ import annotations

from dataclasses import dataclass, field

from .manifest import MANIFEST, STANDARD_VERSION, Section


def _resolve(snapshot: dict, path: str):
    cur = snapshot
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        return False
    return True


@dataclass
class ConformanceResult:
    level: str
    conformant: bool
    missing_sections: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    stale: bool = False
    omitted: list[str] = field(default_factory=list)


def check_conformance(level: str, snapshot: dict, *, profile_version: int | None = None) -> ConformanceResult:
    sections: list[Section] = MANIFEST[level]
    missing_sections: list[str] = []
    missing_fields: list[str] = []
    for sec in sections:
        sec_has_any = False
        for f in sec.fields:
            present = _present(_resolve(snapshot, f.path))
            if present:
                sec_has_any = True
            elif f.required and sec.required:
                missing_fields.append(f.path)
        if sec.required and not sec_has_any:
            missing_sections.append(sec.id)
    stale = profile_version is not None and profile_version < STANDARD_VERSION
    conformant = not missing_fields and not missing_sections and not stale
    return ConformanceResult(
        level=level, conformant=conformant,
        missing_sections=missing_sections, missing_fields=missing_fields, stale=stale,
    )
```

- [ ] **Step 4: Write `__init__.py`:**

```python
from .conformance import ConformanceResult, check_conformance
from .manifest import MANIFEST, STANDARD_VERSION, Field, Section

__all__ = ["MANIFEST", "STANDARD_VERSION", "Field", "Section", "ConformanceResult", "check_conformance"]
```

- [ ] **Step 5: Run the test, expect PASS.** Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py -q`

- [ ] **Step 6: Commit.**

---

### Task 3: Certify the MIT trio conforms (the gold-standard gate)

**Files:**
- Modify: `unipaith-backend/tests/test_profile_standard.py`

- [ ] **Step 1: Add the certification test.** It builds each level's snapshot from the MIT module constants and asserts conformance.

```python
from unipaith.data import mit_profile as M

def _program_snapshot(slug: str) -> dict:
    spec = next(p for p in M.PROGRAMS if p["slug"] == slug)
    return {
        "program_name": M._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": M._DESC_RICH_BY_SLUG.get(slug) or spec["description"],
        "website_url": M._WEBSITE_BY_SLUG.get(slug),
        "application_requirements": M._REQ_BY_SLUG.get(slug, M._REQ_MBA),
        "cost_data": M._COST_BY_SLUG.get(slug, {}),
        "outcomes_data": M._OUTCOMES_BY_SLUG.get(slug, {}),
        "class_profile": M._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty": M._FACULTY_BY_SLUG.get(slug, {}),
        "reviews": M._REVIEWS_BY_SLUG.get(slug, {}),
    }

def test_mban_program_is_conformant():
    res = check_conformance("program", _program_snapshot("mit-sloan-mban"), profile_version=STANDARD_VERSION)
    assert res.conformant, f"MBAn must be the gold standard; gaps: {res.missing_fields} {res.missing_sections}"

def test_sloan_school_is_conformant():
    snap = {
        "name": "MIT Sloan School of Management",
        "description": next(s for s in M.SCHOOLS if "Sloan" in s["name"]).get("description", ""),
        "website_url": M._SCHOOL_WEBSITE.get("MIT Sloan School of Management"),
        "about_detail": M._SLOAN_ABOUT_DETAIL,
        "content_sources": M._SLOAN_CONTENT,
    }
    res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
    assert res.conformant, f"Sloan gaps: {res.missing_fields} {res.missing_sections}"

def test_mit_institution_is_conformant():
    snap = {
        "description_text": M.DESCRIPTION,
        "student_body_size": M.UNDERGRAD_COUNT,
        "media_gallery": [M._CAMPUS_PHOTO],
        "ranking_data": M.RANKING_DATA,
        "school_outcomes": M.SCHOOL_OUTCOMES,
        "content_sources": {"news_rss": "x", "events_feed": {}, "social": {}},
    }
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    assert res.conformant, f"MIT gaps: {res.missing_fields} {res.missing_sections}"
```

- [ ] **Step 2: Run the three certification tests.** Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py -q`. Expected: all pass. **If a field path is wrong, fix the manifest path to match the real MIT key — the MIT trio is the source of truth, so a failure means the manifest is wrong, not MIT.**

- [ ] **Step 3: Commit.**

---

### Task 4: Manifest JSON export + frontend render-parity test

**Files:**
- Create: `unipaith-backend/src/unipaith/profile_standard/export_manifest.py`
- Create: `frontend/src/generated/profile-manifest.json`
- Create: `frontend/src/test/profile-manifest-parity.test.ts`

- [ ] **Step 1: Write `export_manifest.py`** that serializes `MANIFEST` (section ids/titles/order + field keys) to `frontend/src/generated/profile-manifest.json`.

```python
import json
from pathlib import Path
from .manifest import MANIFEST, STANDARD_VERSION

def build() -> dict:
    return {
        "version": STANDARD_VERSION,
        "levels": {
            level: [
                {"id": s.id, "title": s.title, "order": s.order, "required": s.required,
                 "widget": s.widget, "fields": [f.key for f in s.fields]}
                for s in secs
            ]
            for level, secs in MANIFEST.items()
        },
    }

def main() -> None:
    out = Path(__file__).resolve().parents[5] / "frontend/src/generated/profile-manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=2) + "\n")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Generate it.** Run: `cd unipaith-backend && PYTHONPATH=src .venv/bin/python -m unipaith.profile_standard.export_manifest` and confirm `frontend/src/generated/profile-manifest.json` exists.

- [ ] **Step 3: Write the parity test** `frontend/src/test/profile-manifest-parity.test.ts` — assert each manifest section id is referenced in the matching detail page source (a smoke-level parity so adding a section to the manifest forces a render block).

```ts
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import manifest from '../generated/profile-manifest.json'

const PAGES: Record<string, string> = {
  institution: 'src/pages/student/institution/InstitutionDetail.tsx',
  school: 'src/pages/student/SchoolSubunitPage.tsx',
  program: 'src/pages/student/ProgramDetailPage.tsx',
}

describe('profile manifest ↔ render parity', () => {
  for (const [level, sections] of Object.entries(manifest.levels)) {
    const src = readFileSync(PAGES[level], 'utf8').toLowerCase()
    for (const sec of sections as any[]) {
      if (!sec.required) continue
      it(`${level}: section "${sec.id}" has a render anchor`, () => {
        const title = String(sec.title).split(' ')[0].toLowerCase()
        expect(src.includes(sec.id) || src.includes(title)).toBe(true)
      })
    }
  }
})
```

- [ ] **Step 4: Run the parity test.** Run: `cd frontend && npx vitest run src/test/profile-manifest-parity.test.ts`. Fix manifest section ids/titles if an anchor is missing (the page is the truth for render; align the manifest's id/title token).

- [ ] **Step 5: Commit.**

---

### Task 5: Sourcing/wording playbook

**Files:**
- Create: `unipaith-backend/src/unipaith/profile_standard/playbook.md`

- [ ] **Step 1: Write `playbook.md`** documenting, per field group, the authoritative source(s), citation format, tone, and the no-fabrication / omit-if-unverifiable rule. (Content authored from the MIT trio's real sources: career-office employment reports for outcomes, registrar for tuition, named ranking bodies for ranks, official school pages for leadership/faculty/research centers.)

- [ ] **Step 2: Commit.**

---

### Task 6: Ship Phase 1

- [ ] **Step 1: Full backend lint + targeted tests.** `cd unipaith-backend && .venv/bin/ruff check src/unipaith/profile_standard tests/test_profile_standard.py && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py -q`
- [ ] **Step 2: Frontend build + parity test.** `cd frontend && npm run build && npx vitest run src/test/profile-manifest-parity.test.ts`
- [ ] **Step 3: Commit, PR, merge, deploy, verify** via the standard pipeline. (No data migration — backend logic + a committed JSON artifact only.)

---

## Self-Review

**Spec coverage:** §3 manifest → Task 1; §3.2 playbook → Task 5; §3.3 versioning → `STANDARD_VERSION` in Task 1 + `profile_version` arg in Task 2; §6 conformance → Tasks 2–3; §6 render parity → Task 4. (§4 shared base, §5 stamp persistence, §7–§9 engine/gate/delivery, §10 propagation, §11 Phases 2–3 are explicitly out of Phase 1 — separate plans.)

**Placeholder scan:** none — every code step has full code; Task 5 playbook content is described with concrete sources.

**Type consistency:** `check_conformance(level, snapshot, profile_version=)` and `ConformanceResult` fields are used identically in Tasks 2 and 3. `Field.path` dotted-resolution matches the snapshots built in Task 3.

**Note on paths:** the `export_manifest.py` output path uses `parents[5]` from `.../src/unipaith/profile_standard/export_manifest.py` → repo root; verify the index during execution and adjust to land at `frontend/src/generated/`.
